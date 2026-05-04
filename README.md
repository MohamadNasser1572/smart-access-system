# Privacy-First Edge AI Smart Access System (Software Version)

Runs 100% locally on your laptop.

## 1) Tech Stack (Exact)
- Language: Python
- Core Libraries: OpenCV, face_recognition, numpy
- Backend/API: FastAPI
- Database: SQLite
- API Testing: Postman
- Optional Bonus: Docker

## 2) System Architecture
Modules:
- Camera Module (`camera.py`)
- Face Recognition Module (`face_recognition_module.py`)
- Risk Engine (`risk_engine.py`)
- API Server (`api.py`)
- Database (`database.py`)

## 3) Project Structure
```text
smart-access-system/
├─ main.py
├─ camera.py
├─ face_recognition_module.py
├─ risk_engine.py
├─ database.py
├─ api.py
├─ Dockerfile
├─ requirements.txt
├─ models/
├─ data/
├─ known_faces/
└─ docs/
```

## 4) Step-by-Step Implementation

### STEP 1 — Setup Environment
```powershell
cd "C:\Users\pc\AI Smart Access System\smart-access-system"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### STEP 2 — Camera Module
Implemented in `camera.py`.
- Captures webcam frames
- Shows live window
- Exits on ESC key

### STEP 3 — Face Recognition Module
Implemented in `face_recognition_module.py`.
- Loads known faces from `known_faces/`
- Generates embeddings with `face_recognition`
- Matches incoming frame embeddings
- Returns recognized name or `Unknown`

### STEP 4 — Risk Engine
Implemented in `risk_engine.py`.
- `Unknown` → `High`
- Known person → `Low`

### STEP 5 — Database (SQLite)
Implemented in `database.py`.
- Auto-creates `system.db`
- Creates `logs` table if missing
- Stores `(name, risk)` events

### STEP 6 — Main System
Implemented in `main.py`.
- Loads faces
- Starts webcam stream
- Recognizes person + computes risk
- Logs each event to SQLite

Run:
```powershell
python main.py
```

### STEP 7 — API (FastAPI)
Implemented in `api.py`.

Run:
```powershell
uvicorn api:app --reload
```

### STEP 8 — Postman Test
- Method: `GET`
- URL: `http://127.0.0.1:8000/logs`
- Returns access logs from `system.db`

### STEP 9 — Docker (Optional Bonus)
```powershell
docker build -t smart-access-system .
docker run --rm smart-access-system
```

### STEP 10 — Demo Checklist
- Webcam feed works
- Face recognition works
- Risk classification appears
- Events are logged in SQLite
- Logs are visible via API endpoint

## 5) Documentation / Report Sections
Use `docs/REPORT_TEMPLATE.md` and include:
- Introduction
- Problem
- Solution
- System Architecture
- Implementation
- UML Diagrams
- Results

## Notes
- Place training face images in `known_faces/` (example: `alice.jpg`).
- If a person image has no detectable face, it is skipped automatically.
- Everything runs locally for privacy-first operation.
