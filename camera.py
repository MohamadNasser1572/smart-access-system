import cv2


def start_camera() -> None:
    cap = cv2.VideoCapture(0)
    window_name = "Camera"

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
