import os
import time as _time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import face_recognition
import numpy as np


known_faces: List[np.ndarray] = []
known_names: List[str] = []

RECOGNITION_TOLERANCE = 0.5
FACE_RESIZE_SCALE = 0.25
DEBUG = os.getenv("SMART_ACCESS_DEBUG", "0").strip().lower() not in {"0", "false", "no", "off"}


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
    global _last_face_seen_at, _last_face_location, _face_gone_since
    known_faces.clear()
    known_names.clear()
    # Reset disappearance tracking so stale "Unknown" state from before the
    # reload doesn't linger into the next recognition cycle.
    _last_face_seen_at = 0.0
    _last_face_location = None
    _face_gone_since = 0.0

    if DEBUG:
        print(f"[debug] load_faces: starting load from '{folder}'")

    if not os.path.isdir(folder):
        if DEBUG:
            print(f"[debug] load_faces: folder '{folder}' does not exist, creating it")
        os.makedirs(folder, exist_ok=True)
        print(f"Known faces folder created at: {folder}")
        return

    if DEBUG:
        print(f"[debug] load_faces: folder exists at '{folder}'")

    grouped_encodings: dict[str, List[np.ndarray]] = {}
    total_files_scanned = 0
    total_faces_found = 0

    for root, dirs, file_names in os.walk(folder):
        if DEBUG:
            print(f"[debug] load_faces: scanning directory '{root}' with {len(dirs)} subdirs, {len(file_names)} files")

        for file_name in file_names:
            total_files_scanned += 1
            if not _is_image_file(file_name):
                if DEBUG:
                    print(f"[debug] load_faces: skipping '{file_name}' (not an image)")
                continue

            file_path = os.path.join(root, file_name)
            person_name = _person_name(folder, file_path)

            if DEBUG:
                print(f"[debug] load_faces: processing '{file_name}' -> person: '{person_name}'")

            try:
                image = face_recognition.load_image_file(file_path)
                if DEBUG:
                    print(f"[debug] load_faces: loaded image from '{file_path}' (shape: {image.shape})")
            except Exception as e:
                print(f"[error] load_faces: failed to load image '{file_path}': {e}")
                continue

            # Detect and encode using the image exactly as face_recognition loaded it.
            # Resizing via cv2 produces arrays that dlib rejects; PIL-loaded arrays are safe.
            try:
                locations = face_recognition.face_locations(image, model="hog")
                if DEBUG:
                    print(f"[debug] load_faces: detected {len(locations)} face(s) in '{file_name}'")

                encodings = face_recognition.face_encodings(image, locations)
                if DEBUG:
                    print(f"[debug] load_faces: extracted {len(encodings)} encoding(s) from '{file_name}'")
            except Exception as ex:
                import traceback

                print(f"[error] load_faces: exception during detection/encoding for '{file_name}': {ex}")
                traceback.print_exc()
                raise

            if not encodings:
                print(f"Skipped {file_name}: no face found")
                continue

            total_faces_found += len(encodings)

            if len(locations) > 1:
                largest_face_index = max(
                    range(len(locations)),
                    key=lambda index: (locations[index][2] - locations[index][0]) * (locations[index][1] - locations[index][3]),
                )
                if DEBUG:
                    print(f"[debug] load_faces: multiple faces detected in '{file_name}', using largest (index {largest_face_index})")
                grouped_encodings.setdefault(person_name, []).append(encodings[largest_face_index])
                continue

            grouped_encodings.setdefault(person_name, []).append(encodings[0])

    if DEBUG:
        print(f"[debug] load_faces: scanned {total_files_scanned} files, found {total_faces_found} total faces")
        print(f"[debug] load_faces: grouped into {len(grouped_encodings)} identities: {list(grouped_encodings.keys())}")

    for person_name, encodings in grouped_encodings.items():
        if DEBUG:
            print(f"[debug] load_faces: averaging {len(encodings)} encoding(s) for '{person_name}'")
        centroid = np.mean(encodings, axis=0).astype(np.float32)
        known_faces.append(np.asarray(centroid, dtype=np.float32))
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


_last_face_seen_at: float = 0.0
_face_gone_since: float = 0.0       # when the face first disappeared this absence
# Only flag after face has been consistently gone this long (ignores quick movement).
_FACE_COVER_DELAY = 0.5
# Stop flagging after this long with no face (person left the frame).
_FACE_DISAPPEAR_WINDOW = 2.0
_last_face_location: Optional[Tuple[int, int, int, int]] = None


def recognize(frame) -> List[FaceDetection]:
    global _last_face_seen_at, _last_face_location, _face_gone_since

    if not known_faces:
        print("No known faces loaded. Add JPG/PNG images to known_faces/ and restart.")
        return []

    small_frame = cv2.resize(frame, None, fx=FACE_RESIZE_SCALE, fy=FACE_RESIZE_SCALE)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
    if not face_locations:
        if DEBUG:
            print("[debug] no faces detected in frame")

        now = _time.monotonic()

        # Record when the face first disappeared (don't overwrite if already tracking absence).
        if _face_gone_since == 0.0 and _last_face_seen_at > 0.0:
            _face_gone_since = now

        # Only flag as covered if the face has been consistently absent for at
        # least _FACE_COVER_DELAY seconds (filters out quick turns/movements).
        absence_duration = now - _face_gone_since if _face_gone_since > 0.0 else 0.0
        elapsed_since_seen = now - _last_face_seen_at

        if (
            _last_face_location is not None
            and absence_duration >= _FACE_COVER_DELAY
            and elapsed_since_seen < _FACE_DISAPPEAR_WINDOW
        ):
            if DEBUG:
                print(f"[debug] face covered for {absence_duration:.2f}s — marking as suspicious unknown")
            return [
                FaceDetection(
                    location=_last_face_location,
                    name="Unknown",
                    confidence=0.0,
                    distance=1.0,
                )
            ]
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

    # Face is visible — reset disappearance tracking.
    if detections:
        _last_face_seen_at = _time.monotonic()
        _last_face_location = detections[0].location
        _face_gone_since = 0.0  # reset so next absence starts a fresh countdown

    return detections
