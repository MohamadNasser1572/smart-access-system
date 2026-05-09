import { useRef, useState } from 'react'
import './EnrollmentForm.css'

function EnrollmentForm({ onSuccess }) {
  const [name, setName] = useState('')
  const [riskLevel, setRiskLevel] = useState('Low')
  const [photo, setPhoto] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const fileInputRef = useRef(null)
  const [cameraActive, setCameraActive] = useState(false)

  const loadPhotoFromBlob = (blob) => {
    setPhoto(blob)
    setPhotoPreview(URL.createObjectURL(blob))
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
      })
      videoRef.current.srcObject = stream
      setError('')
      setCameraActive(true)
    } catch (err) {
      const denied = err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError'
      setError(
        denied
          ? 'Camera permission was denied. Use Upload Photo instead, or allow camera access in your browser settings.'
          : 'Cannot access camera: ' + err.message,
      )
    }
  }

  const capturePhoto = () => {
    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    context.drawImage(video, 0, 0)

    canvas.toBlob((blob) => {
      loadPhotoFromBlob(blob)
      stopCamera()
    }, 'image/jpeg')
  }

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }

    setError('')
    setCameraActive(false)
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop())
      videoRef.current.srcObject = null
    }

    loadPhotoFromBlob(file)
  }

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop())
      videoRef.current.srcObject = null
      setCameraActive(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim()) {
      setError('Please enter a name')
      return
    }

    if (!photo) {
      setError('Please take a photo')
      return
    }

    setLoading(true)

    try {
      const reader = new FileReader()
      reader.onloadend = async () => {
        const base64Photo = reader.result.split(',')[1]

        const response = await fetch('http://127.0.0.1:8000/faces/enroll', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: name.trim(),
            risk_level: riskLevel,
            photo_base64: base64Photo,
          }),
        })

        const data = await response.json()

        if (!response.ok) {
          setError(data.detail || 'Failed to enroll face')
          return
        }

        setName('')
        setRiskLevel('Low')
        setPhoto(null)
        setPhotoPreview(null)
        onSuccess()
      }
      reader.readAsDataURL(photo)
    } catch (err) {
      setError('Error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="enrollment-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="name">Name:</label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter person's name"
          disabled={loading || cameraActive}
        />
      </div>

      <div className="form-group">
        <label htmlFor="riskLevel">Risk Level:</label>
        <select
          id="riskLevel"
          value={riskLevel}
          onChange={(e) => setRiskLevel(e.target.value)}
          disabled={loading || cameraActive}
        >
          <option value="Low">Low (Known/Trusted)</option>
          <option value="Medium">Medium (Caution)</option>
          <option value="High">High (Restricted)</option>
        </select>
      </div>

      <div className="camera-section">
        {!cameraActive ? (
          <div className="camera-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={startCamera}
              disabled={loading}
            >
              📷 Start Camera
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              ⬆ Upload Photo
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="user"
              onChange={handleFileSelect}
              className="hidden-file-input"
            />
          </div>
        ) : (
          <div className="camera-container">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="video-feed"
            />
            <button
              type="button"
              className="btn btn-capture"
              onClick={capturePhoto}
            >
              📸 Capture Photo
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={stopCamera}
            >
              ✕ Cancel
            </button>
          </div>
        )}
      </div>

      {photoPreview && (
        <div className="photo-preview">
          <img src={photoPreview} alt="Captured" />
          <p>Photo captured ✓</p>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {error && <div className="error-message">{error}</div>}

      <button
        type="submit"
        className="btn btn-success"
        disabled={loading || !name || !photo}
      >
        {loading ? 'Enrolling...' : '✓ Enroll Face'}
      </button>
    </form>
  )
}

export default EnrollmentForm
