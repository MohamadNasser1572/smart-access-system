from threading import Thread, Event
import time
import queue as _queue
from typing import Optional

# Set by run_system() once load_faces() + camera open have both succeeded.
_system_ready_event: Event = Event()

from database import log_event, stop_logging
from risk_engine import calculate_risk


# Runner control globals
_runner_thread: Optional[Thread] = None
_stop_event: Event = Event()
_last_start_error: Optional[str] = None
# One entry per person (keyed by name); overwritten every detection so the
# frontend gets a reactive snapshot rather than a growing history list.
_recent_detections: dict = {}
# Tracks the last risk level that was written to the DB for each name so we
# only insert a new log row when the risk actually changes.
_last_logged_risk: dict = {}
# Latest cropped JPEG of an unknown face — served by /api/unknown-face.
_latest_unknown_face_jpg: Optional[bytes] = None
# Latest annotated frame JPEG — served by /api/video-feed as an MJPEG stream.
_latest_frame_jpg: Optional[bytes] = None


def _classify_detection_risk(detection) -> str:
    if detection.name.strip().lower() != "unknown":
        return calculate_risk(detection.name)

    if detection.distance >= 0.95:
        return "High"

    return "Medium"


def run_system(stop_event: Optional[Event] = None) -> None:
    import os
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")

    import cv2
    global _last_start_error, _system_ready_event, _latest_unknown_face_jpg, _latest_frame_jpg

    try:
        from face_recognition_module import load_faces, recognize
    except Exception as e:
        _last_start_error = f"Failed to import face recognition: {e}"
        print(f"[error] {_last_start_error}")
        return

    try:
        load_faces()
    except Exception as e:
        _last_start_error = f"load_faces() failed: {e}"
        print(f"[error] {_last_start_error}")
        return

    cap = None
    for cam_index in range(3):
        candidate = cv2.VideoCapture(cam_index)
        if candidate.isOpened():
            cap = candidate
            break
        candidate.release()
    if cap is None:
        _last_start_error = "Unable to open webcam (tried indices 0, 1, 2)"
        print("[error] unable to open webcam on indices 0, 1, or 2")
        return

    # Cap resolution at 640×480 — reduces frame size 3× vs typical 1280×720
    # default, making frame copy, annotation, display, and recognition all faster.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    _system_ready_event.set()

    # Recognition runs in its own thread so the camera loop never blocks on dlib.
    frame_in: _queue.Queue = _queue.Queue(maxsize=1)
    detections_out: _queue.Queue = _queue.Queue(maxsize=1)

    def _recognition_worker() -> None:
        while not (stop_event is not None and stop_event.is_set()):
            try:
                frame = frame_in.get(timeout=0.1)
            except _queue.Empty:
                continue
            results = recognize(frame)
            # Always replace with the freshest result — discard stale.
            try:
                detections_out.get_nowait()
            except _queue.Empty:
                pass
            detections_out.put(results)

    rec_thread = Thread(target=_recognition_worker, daemon=True)
    rec_thread.start()

    frame_count = 0
    last_detections = []

    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break

            ret, frame = cap.read()
            if not ret:
                if frame_count == 0:
                    _last_start_error = "Unable to read from webcam"
                    print("[error] unable to read from webcam")
                break

            frame_count += 1

            # Send every 3rd frame to the recognition worker (non-blocking).
            if frame_count % 3 == 0:
                try:
                    frame_in.put_nowait(frame.copy())
                except _queue.Full:
                    pass  # worker still busy; keep current last_detections

            # Pick up whatever the worker finished last (non-blocking).
            try:
                last_detections = detections_out.get_nowait()
            except _queue.Empty:
                pass

            # Only copy the frame if there's something to draw on it.
            annotated_frame = frame.copy() if last_detections else frame

            # Compute risk once per detection and reuse for drawing, logging, and
            # the detections dict — avoids a duplicate DB lookup each cycle.
            is_recognition_frame = frame_count % 3 == 0
            new_detection_entries = {} if is_recognition_frame else None

            for detection in last_detections:
                top, right, bottom, left = detection.location
                risk = _classify_detection_risk(detection)
                label = f"{detection.name} | {detection.confidence:.1f}% | {risk}"
                risk_normalized = risk.strip().lower()
                is_unknown = detection.name.strip().lower() == "unknown"

                if is_unknown:
                    box_color = (0, 165, 255) if risk_normalized == "medium" else (0, 0, 255)
                elif risk_normalized == "low":
                    box_color = (0, 255, 0)
                elif risk_normalized == "medium":
                    box_color = (0, 165, 255)
                else:
                    box_color = (0, 0, 255)

                cv2.rectangle(annotated_frame, (left, top), (right, bottom), box_color, 2)
                cv2.rectangle(annotated_frame, (left, bottom - 28), (right, bottom), box_color, cv2.FILLED)
                cv2.putText(
                    annotated_frame,
                    label,
                    (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

                if is_recognition_frame:
                    if is_unknown:
                        print(f"Detected: Unknown | Distance: {detection.distance:.4f} | Risk: {risk}")
                        h, w = frame.shape[:2]
                        pad = 30
                        crop = frame[
                            max(0, top - pad):min(h, bottom + pad),
                            max(0, left - pad):min(w, right + pad),
                        ]
                        if crop.size > 0:
                            ok, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            if ok:
                                _latest_unknown_face_jpg = buf.tobytes()
                    else:
                        print(
                            f"Detected: {detection.name} | Match: {detection.confidence:.1f}% | "
                            f"Distance: {detection.distance:.4f} | Risk: {risk}"
                        )

                    if _last_logged_risk.get(detection.name) != risk:
                        log_event(detection.name, risk)
                        _last_logged_risk[detection.name] = risk

                    new_detection_entries[detection.name] = {
                        "name": detection.name,
                        "confidence": detection.confidence,
                        "distance": detection.distance,
                        "risk": risk,
                    }

            # Rebuild the live detections dict from scratch each recognition cycle.
            if is_recognition_frame:
                _recent_detections.clear()
                _recent_detections.update(new_detection_entries)

            # Encode the annotated frame for the browser MJPEG stream.
            ok, buf = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
            if ok:
                _latest_frame_jpg = buf.tobytes()
    finally:
        stop_logging()
        cap.release()
        global _runner_thread
        _runner_thread = None
        _recent_detections.clear()
        _last_logged_risk.clear()
        _latest_unknown_face_jpg = None
        _latest_frame_jpg = None


def start_system() -> bool:
    global _runner_thread, _stop_event, _last_start_error, _system_ready_event
    if _runner_thread is not None and _runner_thread.is_alive():
        return False

    _last_start_error = None
    _system_ready_event = Event()
    _stop_event = Event()
    _runner_thread = Thread(target=run_system, args=(_stop_event,), daemon=True)
    _runner_thread.start()

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if _system_ready_event.is_set():
            return True
        if not _runner_thread.is_alive():
            _runner_thread = None
            return False
        time.sleep(0.1)

    _stop_event.set()
    _runner_thread = None
    _last_start_error = "System took too long to start"
    return False


def stop_system(timeout: float = 5.0) -> bool:
    global _runner_thread, _stop_event
    if _runner_thread is None or not _runner_thread.is_alive():
        return False

    _stop_event.set()
    _runner_thread.join(timeout=timeout)
    stopped = not _runner_thread.is_alive()
    if stopped:
        _runner_thread = None
    return stopped


def is_system_running() -> bool:
    return _runner_thread is not None and _runner_thread.is_alive()


def get_recent_detections() -> list:
    return list(_recent_detections.values())


def get_latest_unknown_face() -> Optional[bytes]:
    return _latest_unknown_face_jpg


def get_latest_frame() -> Optional[bytes]:
    return _latest_frame_jpg


def get_last_start_error() -> Optional[str]:
    return _last_start_error


if __name__ == "__main__":
    run_system()
