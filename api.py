import os
import base64

# Limit BLAS/OMP threads early to reduce memory pressure when native libs load
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from typing import List, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from database import DB_PATH, add_face, remove_face, update_face_risk, get_all_faces, get_face_risk, get_logs

app = FastAPI(title="Smart Access System API")

# Bug 4 fix: allow_credentials=True is incompatible with wildcard origin per the
# CORS spec — browsers silently drop credentialed responses. Use explicit origins
# or drop allow_credentials. For a local dev tool we drop allow_credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


# Bug 3 fix: use the shared DB helper (with lock) instead of a raw sqlite3 connection.
@app.get("/logs")
def get_logs_endpoint():
    return get_logs()


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
        import numpy as np
        import cv2
        import face_recognition

        photo_data = base64.b64decode(request.photo_base64)
        nparr = np.frombuffer(photo_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        rgb_frame = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")

        if not face_locations:
            raise HTTPException(status_code=400, detail="No face detected in photo")

        if len(face_locations) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected. Please provide one face per photo")

        # Bug 2 fix: reject names that would escape the known_faces/ directory.
        safe_name = os.path.normpath(request.name.strip())
        if os.sep in safe_name or safe_name.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid character in name")

        person_dir = os.path.join(known_faces_dir, safe_name)
        os.makedirs(person_dir, exist_ok=True)

        existing_indices = []
        for file_name in os.listdir(person_dir):
            base_name, extension = os.path.splitext(file_name)
            if extension.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"} and base_name.isdigit():
                existing_indices.append(int(base_name))

        next_index = max(existing_indices, default=0) + 1
        photo_path = os.path.join(person_dir, f"{next_index}.jpg")
        cv2.imwrite(photo_path, frame)

        if not add_face(safe_name, request.risk_level):
            raise HTTPException(status_code=500, detail=f"Failed to save face record for '{safe_name}'")

        return {
            "status": "enrolled",
            "name": safe_name,
            "risk_level": request.risk_level,
            "photo_index": next_index,
            "message": f"Saved photo {next_index} for '{safe_name}'",
        }
    except HTTPException:
        raise
    except Exception:
        # Bug 5 fix: don't leak internal exception details to the client.
        raise HTTPException(status_code=500, detail="Failed to enroll face")


@app.get("/status")
def get_status() -> dict:
    try:
        faces = get_all_faces()
        loaded_identities = [name for name, _ in faces]
        loaded_count = len(loaded_identities)
    except Exception:
        loaded_identities = []
        loaded_count = 0

    try:
        import main as main_module
        system_running = main_module.is_system_running()
    except Exception:
        system_running = False

    return {
        "status": "running",
        "loaded_identities": loaded_identities,
        "loaded_count": loaded_count,
        "system_running": system_running,
        "api_version": "1.0",
    }


@app.post("/system/start")
def api_start_system() -> dict:
    try:
        import main as main_module

        started = main_module.start_system()
        if not started:
            error = main_module.get_last_start_error()
            if error:
                return {"status": "failed", "detail": error}
            return {"status": "already_running"}

        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/system/stop")
def api_stop_system() -> dict:
    try:
        import main as main_module

        stopped = main_module.stop_system()
        if not stopped:
            return {"status": "not_running"}

        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


class RiskUpdateRequest(BaseModel):
    risk_level: str


@app.patch("/faces/{name}/risk")
def update_face_risk_endpoint(name: str, request: RiskUpdateRequest) -> dict:
    if request.risk_level not in ["Low", "Medium", "High"]:
        raise HTTPException(status_code=400, detail="Risk level must be Low, Medium, or High")

    safe_name = os.path.normpath(name.strip())
    if os.sep in safe_name or safe_name.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid character in name")

    success = update_face_risk(safe_name, request.risk_level)
    if not success:
        raise HTTPException(status_code=404, detail=f"Face '{safe_name}' not found")

    return {"status": "updated", "name": safe_name, "risk_level": request.risk_level}


@app.delete("/faces/{name}")
def remove_enrolled_face(name: str) -> dict:
    # Bug 2 fix: validate name before using it as a filesystem path.
    safe_name = os.path.normpath(name.strip())
    if os.sep in safe_name or safe_name.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid character in name")

    success = remove_face(safe_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Face '{safe_name}' not found")

    person_dir = os.path.join("known_faces", safe_name)
    if os.path.isdir(person_dir):
        import shutil
        shutil.rmtree(person_dir)

    return {
        "status": "removed",
        "name": safe_name,
        "message": f"Face '{safe_name}' removed successfully",
    }


@app.get("/detections")
def get_detections() -> dict:
    try:
        import main as main_module
        recent = main_module.get_recent_detections()
        return {"detections": recent}
    except Exception as e:
        return {"detections": [], "error": str(e)}


@app.get("/frame")
def get_frame():
    """Latest annotated camera frame as a JPEG. Poll this rapidly for live video."""
    try:
        import main as main_module
        jpg = main_module.get_latest_frame()
        if jpg is None:
            raise HTTPException(status_code=503, detail="No frame available")
        return Response(
            content=jpg,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unknown-face")
def get_unknown_face():
    try:
        import main as main_module
        jpg = main_module.get_latest_unknown_face()
        if jpg is None:
            raise HTTPException(status_code=404, detail="No unknown face captured yet")
        return Response(content=jpg, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
