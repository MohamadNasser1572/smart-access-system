import cv2

from database import log_event
from face_recognition_module import load_faces, recognize
from risk_engine import calculate_risk


def run_system() -> None:
    load_faces()

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        name = recognize(frame)
        risk = calculate_risk(name)

        print(f"{name} - {risk}")
        log_event(name, risk)

        cv2.imshow("System", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_system()
