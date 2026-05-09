# Smart Access System - React Frontend

A beautiful React UI for managing face enrollment, removal, and risk level configuration.

## Features

- 📷 **Live Camera Capture**: Take photos directly from your browser
- 👤 **Add Known Faces**: Enroll faces with adjustable risk levels (Low, Medium, High)
- 🗑️ **Remove Faces**: Delete enrolled faces with confirmation
- 📋 **View All Faces**: Display all known faces with their risk levels
- 🎨 **Modern UI**: Clean, responsive design with gradient styling
- ✅ **Real-time Updates**: Instant feedback after enrollment/removal

## Quick Start

### Prerequisites
- Node.js 16+ and npm

### Installation & Setup

```bash
cd frontend
npm install
npm run dev
```

The React app will start at `http://localhost:3000`

**Make sure the FastAPI backend is running first:**
```bash
# In the parent directory
python main.py  # or START.ps1 option 4
# In another terminal
uvicorn api:app --reload
```

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── EnrollmentForm.jsx      # Camera capture & enrollment form
│   │   ├── EnrollmentForm.css
│   │   ├── FacesList.jsx           # Display & remove known faces
│   │   └── FacesList.css
│   ├── App.jsx                     # Main app component
│   ├── App.css
│   └── main.jsx                    # React entry point
├── index.html
├── vite.config.js                  # Vite configuration
├── package.json
└── .gitignore
```

## API Integration

The frontend connects to the FastAPI backend at `http://127.0.0.1:8000`:

- **GET `/faces`** - List all enrolled faces
- **POST `/faces/enroll`** - Enroll a new face with photo
- **DELETE `/faces/{name}`** - Remove a face

## Usage

1. **Enroll a Face**:
   - Enter the person's name
   - Select their risk level (Low/Medium/High)
   - Click "Start Camera"
   - Take a photo when ready
   - Click "Enroll Face"

2. **View Known Faces**:
   - All enrolled faces appear on the right panel
   - Risk level shown as colored badge

3. **Remove a Face**:
   - Click the "🗑️ Remove" button on any face card
   - Confirm the deletion

## Styling

- **Gradient Background**: Purple/blue gradient theme
- **Responsive Grid**: Auto-adapts to screen size
- **Risk Level Colors**:
  - 🟢 Low: Green
  - 🟠 Medium: Orange
  - 🔴 High: Red

## Notes

- Camera access requires HTTPS in production (HTTP works locally)
- Photos are sent as base64 to the backend
- Face detection happens server-side for consistency
