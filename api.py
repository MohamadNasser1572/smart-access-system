import base64
import io
import os
import sqlite3
from typing import List, Tuple

import cv2
import face_recognition
import numpy as np
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import DB_PATH, add_face, remove_face, get_all_faces, get_face_risk

app = FastAPI(title="Smart Access System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EnrollRequest(BaseModel):
    name: str
    risk_level: str
    photo_base64: str


class FaceInfo(BaseModel):
    name: str
    risk_level: str


@app.get("/logs")
def get_logs() -> List[Tuple[int, str, str]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            risk TEXT
        )
        """
    )
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.get("/faces")
def list_faces() -> List[FaceInfo]:
    faces = get_all_faces()
    return [FaceInfo(name=name, risk_level=risk_level) for name, risk_level in faces]


@app.post("/faces/enroll")
def enroll_face(request: EnrollRequest) -> dict:
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    if request.risk_level not in ["Low", "Medium", "High"]:
        raise HTTPException(status_code=400, detail="Risk level must be Low, Medium, or High")

    known_faces_dir = "known_faces"
    os.makedirs(known_faces_dir, exist_ok=True)

    try:
        photo_data = base64.b64decode(request.photo_base64)
        nparr = np.frombuffer(photo_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")

        if not face_locations:
            raise HTTPException(status_code=400, detail="No face detected in photo")

        if len(face_locations) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please provide one face per photo")

        person_dir = os.path.join(known_faces_dir, request.name)
        os.makedirs(person_dir, exist_ok=True)

        photo_path = os.path.join(person_dir, f"1.jpg")
        cv2.imwrite(photo_path, frame)

        success = add_face(request.name, request.risk_level)
        if not success:
            raise HTTPException(status_code=400, detail=f"Face '{request.name}' already enrolled")

        return {
            "status": "enrolled",
            "name": request.name,
            "risk_level": request.risk_level,
            "message": f"Face '{request.name}' enrolled successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enroll face: {str(e)}")


@app.get("/status")
def get_status() -> dict:
    from face_recognition_module import known_names, known_faces as loaded_faces
    return {
        "status": "running",
        "loaded_identities": known_names,
        "loaded_count": len(loaded_faces),
        "api_version": "1.0"
    }


@app.post("/reload-faces")
def reload_faces_endpoint() -> dict:
    from face_recognition_module import load_faces as reload_fn, known_names, known_faces as loaded_faces
    try:
        reload_fn()
        return {
            "status": "reloaded",
            "loaded_identities": known_names,
            "loaded_count": len(loaded_faces),
            "message": "Known faces reloaded from disk",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload faces: {str(e)}")


@app.delete("/faces/{name}")
def remove_enrolled_face(name: str) -> dict:
    success = remove_face(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Face '{name}' not found")

    person_dir = os.path.join("known_faces", name)
    if os.path.isdir(person_dir):
        import shutil
        shutil.rmtree(person_dir)

    return {
        "status": "removed",
        "name": name,
        "message": f"Face '{name}' removed successfully",
    }
