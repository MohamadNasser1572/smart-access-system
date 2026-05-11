from threading import Thread, Event
import time
from typing import Optional

from database import log_event, stop_logging
from risk_engine import calculate_risk


# Runner control globals
_runner_thread: Optional[Thread] = None
_stop_event: Event = Event()
_last_start_error: Optional[str] = None
# Store recent detections for UI display
_recent_detections: list = []
_MAX_DETECTIONS = 50


def run_system(stop_event: Optional[Event] = None) -> None:
    """Main camera loop. If `stop_event` is provided, the loop will check it
    and exit when set. If not provided, behavior is unchanged and relies on
    window close / ESC key to stop."""

    # Limit BLAS/OMP threads to reduce memory pressure when loading models
    import os
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")

    # Import heavy image/face libs lazily so importing this module doesn't
    # load OpenBLAS/dlib at API import time.
    import cv2
    try:
        from face_recognition_module import load_faces, recognize
    except Exception as e:
        print(f"[error] failed to import face_recognition_module: {e}")
        return

    try:
        load_faces()
    except Exception as e:
        print(f"[error] load_faces() failed: {e}")
        return

    global _last_start_error

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        _last_start_error = "Unable to open webcam"
        print("[error] unable to open webcam")
        return

    window_name = "System"
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

            if frame_count % 3 == 0:
                last_detections = recognize(frame)

            annotated_frame = frame.copy()

            for detection in last_detections:
                top, right, bottom, left = detection.location
                risk = calculate_risk(detection.name)
                label = f"{detection.name} | {detection.confidence:.1f}% | {risk}"
                cv2.rectangle(annotated_frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(annotated_frame, (left, bottom - 28), (right, bottom), (0, 0, 255), cv2.FILLED)
                cv2.putText(
                    annotated_frame,
                    label,
                    (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )
                if frame_count % 3 == 0:
                    if detection.name == "Unknown":
                        print(f"Detected: Unknown | Distance: {detection.distance:.4f} | Risk: {risk}")
                        _recent_detections.append({
                            "name": "Unknown",
                            "confidence": 0.0,
                            "distance": detection.distance,
                            "risk": risk,
                        })
                    else:
                        print(
                            f"Detected: {detection.name} | Match: {detection.confidence:.1f}% | "
                            f"Distance: {detection.distance:.4f} | Risk: {risk}"
                        )
                        _recent_detections.append({
                            "name": detection.name,
                            "confidence": detection.confidence,
                            "distance": detection.distance,
                            "risk": risk,
                        })
                    log_event(detection.name, risk)
            # Keep the buffer from growing indefinitely
            if len(_recent_detections) > _MAX_DETECTIONS:
                _recent_detections.pop(0)
            cv2.imshow(window_name, annotated_frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        stop_logging()
        cap.release()
        cv2.destroyAllWindows()


def start_system() -> bool:
    """Start the camera system in a background thread. Returns True if started, False if already running."""
    global _runner_thread, _stop_event, _last_start_error
    if _runner_thread is not None and _runner_thread.is_alive():
        return False

    _last_start_error = None
    _stop_event = Event()
    _runner_thread = Thread(target=run_system, args=(_stop_event,), daemon=True)
    _runner_thread.start()

    for _ in range(20):
        if not _runner_thread.is_alive():
            _runner_thread = None
            return False
        time.sleep(0.05)

    return True


def stop_system(timeout: float = 5.0) -> bool:
    """Signal the running system to stop and wait up to `timeout` seconds for it to join."""
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
    """Return copy of recent detections."""
    return list(_recent_detections)


def get_last_start_error() -> Optional[str]:
    return _last_start_error


if __name__ == "__main__":
    # allow running directly for local testing
    run_system()
