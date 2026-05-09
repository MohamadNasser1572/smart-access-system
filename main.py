import cv2

from database import log_event, stop_logging
from face_recognition_module import load_faces, recognize
from risk_engine import calculate_risk


def run_system() -> None:
    load_faces()

    cap = cv2.VideoCapture(0)
    window_name = "System"
    frame_count = 0
    last_detections = []

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
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
                    else:
                        print(
                            f"Detected: {detection.name} | Match: {detection.confidence:.1f}% | "
                            f"Distance: {detection.distance:.4f} | Risk: {risk}"
                        )
                    log_event(detection.name, risk)

            cv2.imshow(window_name, annotated_frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        stop_logging()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run_system()
