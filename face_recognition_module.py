import os
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import face_recognition
import numpy as np


known_faces: List[np.ndarray] = []
known_names: List[str] = []

RECOGNITION_TOLERANCE = 0.5
FACE_RESIZE_SCALE = 0.25
DEBUG = os.getenv("SMART_ACCESS_DEBUG", "1").strip().lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class FaceDetection:
    location: Tuple[int, int, int, int]
    name: str
    confidence: float
    distance: float


def _is_image_file(file_name: str) -> bool:
    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp")
    return file_name.lower().endswith(valid_extensions)


def _person_name(root: str, file_path: str) -> str:
    relative_path = os.path.relpath(file_path, root)
    parts = relative_path.split(os.sep)
    if len(parts) > 1:
        return parts[0]
    return os.path.splitext(parts[-1])[0]


def load_faces(folder: str = "known_faces") -> None:
    known_faces.clear()
    known_names.clear()

    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
        print(f"Known faces folder created at: {folder}")
        return

    grouped_encodings: dict[str, List[np.ndarray]] = {}

    for root, _, file_names in os.walk(folder):
        for file_name in file_names:
            if not _is_image_file(file_name):
                continue

            file_path = os.path.join(root, file_name)
            person_name = _person_name(folder, file_path)

            image = face_recognition.load_image_file(file_path)
            locations = face_recognition.face_locations(image, model="hog")
            encodings = face_recognition.face_encodings(image, locations)

            if not encodings:
                print(f"Skipped {file_name}: no face found")
                continue

            if len(locations) > 1:
                largest_face_index = max(
                    range(len(locations)),
                    key=lambda index: (locations[index][2] - locations[index][0]) * (locations[index][1] - locations[index][3]),
                )
                grouped_encodings.setdefault(person_name, []).append(encodings[largest_face_index])
                continue

            grouped_encodings.setdefault(person_name, []).append(encodings[0])

    for person_name, encodings in grouped_encodings.items():
        centroid = np.mean(encodings, axis=0)
        known_faces.append(np.asarray(centroid, dtype=np.float64))
        known_names.append(person_name)

    print(f"Loaded {len(known_faces)} known face(s)")
    if DEBUG:
        print(f"[debug] enrollment identities: {', '.join(known_names) if known_names else 'none'}")


def _best_match(face_encoding: np.ndarray) -> Tuple[str, float, float]:
    if not known_faces:
        return "Unknown", 0.0, 0.0

    distances = face_recognition.face_distance(known_faces, face_encoding)
    best_index = int(np.argmin(distances))
    best_distance = float(distances[best_index])

    if best_distance > RECOGNITION_TOLERANCE:
        return "Unknown", 0.0, best_distance

    confidence = max(0.0, 1.0 - (best_distance / RECOGNITION_TOLERANCE)) * 100.0
    return known_names[best_index], round(confidence, 1), best_distance


def recognize(frame) -> List[FaceDetection]:
    if not known_faces:
        print("No known faces loaded. Add JPG/PNG images to known_faces/ and restart.")
        return []

    small_frame = cv2.resize(frame, None, fx=FACE_RESIZE_SCALE, fy=FACE_RESIZE_SCALE)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
    if not face_locations:
        if DEBUG:
            print("[debug] no faces detected in frame")
        return []

    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    if not face_encodings:
        if DEBUG:
            print("[debug] face locations found, but encodings failed")
        return []

    detections: List[FaceDetection] = []
    scale = int(round(1 / FACE_RESIZE_SCALE))

    for location, face_encoding in zip(face_locations, face_encodings):
        name, confidence, distance = _best_match(face_encoding)
        top, right, bottom, left = location
        original_location = (top * scale, right * scale, bottom * scale, left * scale)
        detections.append(
            FaceDetection(
                location=original_location,
                name=name,
                confidence=confidence,
                distance=round(distance, 4),
            )
        )

        if DEBUG:
            print(
                f"[debug] face: name={name} confidence={confidence:.1f}% distance={distance:.4f} location={original_location}"
            )

    return detections
