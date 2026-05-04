import os
from typing import List

import face_recognition
import cv2


known_faces: List = []
known_names: List[str] = []


def load_faces(folder: str = "known_faces") -> None:
    known_faces.clear()
    known_names.clear()

    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
        return

    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if not os.path.isfile(file_path):
            continue

        # Skip non-image files
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        if not file_name.lower().endswith(valid_extensions):
            continue

        image = face_recognition.load_image_file(file_path)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            continue

        known_faces.append(encodings[0])
        known_names.append(os.path.splitext(file_name)[0])


def recognize(frame):
    rgb = frame[:, :, ::-1]
    # Use OpenCV cascade for face detection (more stable than dlib)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        return "Unknown"
    
    # For each detected face, get encoding and compare
    for (x, y, w, h) in faces:
        # Crop face region
        face_image = rgb[y:y+h, x:x+w]
        
        try:
            # Encode this face
            face_encodings = face_recognition.face_encodings(face_image)
            if len(face_encodings) == 0:
                continue
                
            face_encoding = face_encodings[0]
            
            # Compare with known faces
            matches = face_recognition.compare_faces(known_faces, face_encoding)
            if True in matches:
                return known_names[matches.index(True)]
        except Exception:
            continue
    
    return "Unknown"
