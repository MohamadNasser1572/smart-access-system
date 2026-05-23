# Privacy-First Edge AI Smart Access System

This project is a local, privacy-first face-recognition access demo that runs entirely on your machine. It detects faces from a webcam, matches them against enrolled identities, computes a simple risk level, and logs events to a local SQLite database.

## Problem Solved

Many access-control demos rely on cloud services. This project demonstrates an on-device solution that preserves privacy by keeping video, face data, and risk decisions local while still providing a usable web UI for enrollment and monitoring.

## What the Project Does

- Captures webcam frames and performs face detection/recognition.
- Lets users enroll identities (multiple photos per person).
- Computes a simple risk level per detection and colors the UI overlay.
- Exposes a small REST API for status, faces, detections, and logs.

## Components & Frameworks

- Backend: Python, FastAPI
- Face stack: OpenCV, face_recognition, numpy
- Database: SQLite (lightweight local storage)
- Frontend: React (Vite)

## Run the Frontend (dev)

1. Open a terminal and go to the frontend folder:

```powershell
cd D:\smart-access-system\frontend
```

2. Install dependencies (first time only):

```powershell
npm install
```

3. Start the dev server (this will also ensure the backend is available):

```powershell
npm run dev
```

4. Open the UI in your browser at `http://localhost:3000`.

Notes:
- The frontend dev script prefers to start the backend automatically. If the API is not running, you can start it manually from the project root (see below).
- Use `localhost` (not `file://` or an IP) so the browser treats the page as a secure context and allows camera access.

## Start the Backend (if needed)

From the project root:

```powershell
cd D:\smart-access-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Or run the API directly with Uvicorn:

```powershell
uvicorn api:app --reload --port 8000
```

## Using the UI: start system & camera

1. Open `http://localhost:3000` in Chrome/Edge/Firefox.
2. Click the **Start System** button in the UI to start background detection (this sends the `/system/start` request to the backend).
3. For enrollment, open the Enrollment panel and either:
	- Click **Start Camera** to allow the browser to use your webcam, then **Capture Photo** to take a picture; or
	- Click **Upload Photo** to provide an image file if camera access is denied or unavailable.
4. If the camera permission is denied, follow browser prompts or allow the site under browser settings (see troubleshooting below).
5. Use the UI monitoring page to see live detections (name, confidence, distance, and risk color).

## Camera troubleshooting

- Ensure the page is opened from `http://localhost:3000` and the browser is allowed to access the camera for that origin.
- Check OS camera permissions (Windows: Settings → Privacy → Camera).
- Close other apps that might be using the camera.
- In DevTools Console, run:

```js
navigator.permissions.query({ name: 'camera' }).then(s => console.log(s.state))
```

## Enrollment notes

- Add multiple clear frontal images per person (the app stores multiple photos per identity in `known_faces/`).
- Enrollment updates the face database and the frontend will reflect new faces after reload or via the Reload Faces action.

## Demo checklist

- Run backend and frontend, open `http://localhost:3000`.
- Click **Start System**, verify camera feed and live detections.
- Enroll a face using camera or upload, verify it appears in the faces list.
- Show logs via API or UI.

## Where to look in the code

- `api.py` — REST endpoints
- `main.py` — system lifecycle and camera loop
- `face_recognition_module.py` — loading & matching faces
- `database.py` — SQLite access and logging
- `frontend/src/components/EnrollmentForm.jsx` — camera + enrollment UI

---

If you want, I can also add a short demo script or a one-page slide deck summarizing the project for your presentation.
