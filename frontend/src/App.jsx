import { useState, useEffect, useRef } from 'react'
import EnrollmentForm from './components/EnrollmentForm'
import FacesList from './components/FacesList'
import './App.css'

function App() {
  const API_BASE = '/api'
  const enrollmentRef = useRef(null)
  const reviewedPromptKeyRef = useRef('')
  const [faces, setFaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [systemRunning, setSystemRunning] = useState(false)
  const [detections, setDetections] = useState([])
  const [reviewPrompt, setReviewPrompt] = useState(null)

  const fetchFaces = async () => {
    try {
      const response = await fetch(`${API_BASE}/faces`)
      const data = await response.json()
      setFaces(data)
    } catch (error) {
      console.error('Failed to fetch faces:', error)
      setMessage('Failed to load faces')
    } finally {
      setLoading(false)
    }
  }

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`)
      const data = await res.json()
      setSystemRunning(Boolean(data.system_running))
    } catch (err) {
      console.error('Failed to fetch status', err)
    }
  }

  const fetchDetections = async () => {
    try {
      const res = await fetch(`${API_BASE}/detections`)
      const data = await res.json()
      const nextDetections = data.detections || []
      setDetections(nextDetections)

      const mediumUnknown = [...nextDetections].reverse().find(
        (det) => det.name === 'Unknown' && String(det.risk).toLowerCase() === 'medium',
      )

      if (mediumUnknown) {
        const promptKey = [
          mediumUnknown.name,
          mediumUnknown.risk,
          Number(mediumUnknown.distance || 0).toFixed(2),
          Number(mediumUnknown.confidence || 0).toFixed(1),
        ].join('|')

        if (reviewedPromptKeyRef.current !== promptKey) {
          setReviewPrompt({ ...mediumUnknown, promptKey })
        }
      }
    } catch (err) {
      console.error('Failed to fetch detections', err)
    }
  }

  const acknowledgePrompt = (nextMessage) => {
    if (reviewPrompt?.promptKey) {
      reviewedPromptKeyRef.current = reviewPrompt.promptKey
    }
    setReviewPrompt(null)
    if (nextMessage) {
      setMessage(nextMessage)
      setTimeout(() => setMessage(''), 4000)
    }
  }

  const handleKnownUnknownFace = () => {
    acknowledgePrompt('If you know this person, enroll them in the form below so they become a known face.')
    enrollmentRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleUnknownUnknownFace = () => {
    acknowledgePrompt('This unknown face will remain suspicious/high risk for now.')
  }

  useEffect(() => {
    fetchFaces()
    fetchStatus()

    // Poll status frequently, but only fetch detections when the system is running.
    const interval = setInterval(() => {
      fetchStatus()
    }, 1000)

    const detectionInterval = setInterval(() => {
      if (systemRunning) {
        fetchDetections()
      }
    }, 1000)

    return () => {
      clearInterval(interval)
      clearInterval(detectionInterval)
    }
  }, [systemRunning])

  const handleEnrollSuccess = () => {
    setMessage('Face enrolled successfully!')
    fetchFaces()
    setTimeout(() => setMessage(''), 3000)
  }

  const handleRemoveSuccess = () => {
    setMessage('Face removed successfully!')
    fetchFaces()
    setTimeout(() => setMessage(''), 3000)
  }

  const startSystem = async () => {
    try {
      const res = await fetch(`${API_BASE}/system/start`, { method: 'POST' })
      const data = await res.json()
      if (data.status === 'started' || data.status === 'already_running') {
        setSystemRunning(true)
        setMessage('System started')
        setTimeout(() => setMessage(''), 2500)
      } else if (data.status === 'failed') {
        setSystemRunning(false)
        setMessage(data.detail ? `Failed to start system: ${data.detail}` : 'Failed to start system')
      }
    } catch (err) {
      console.error('Failed to start system', err)
      setMessage('Failed to start system')
    }
  }

  const stopSystem = async () => {
    try {
      const res = await fetch(`${API_BASE}/system/stop`, { method: 'POST' })
      const data = await res.json()
      if (data.status === 'stopped' || data.status === 'not_running') {
        setSystemRunning(false)
        setMessage('System stopped')
        setTimeout(() => setMessage(''), 2500)
      }
    } catch (err) {
      console.error('Failed to stop system', err)
      setMessage('Failed to stop system')
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Smart Access System</h1>
        <p>Face Enrollment Manager</p>
        <div style={{ marginLeft: '16px' }}>
          {!systemRunning ? (
            <button className="start-button" onClick={startSystem}>Start System</button>
          ) : (
            <button className="start-button" onClick={stopSystem}>Stop System</button>
          )}
        </div>
      </header>

      {message && <div className="message-banner">{message}</div>}

      <main className="app-main">
        <section className="section" ref={enrollmentRef}>
          <h2>Enroll New Face</h2>
          <EnrollmentForm onSuccess={handleEnrollSuccess} />
        </section>

        <section className="section">
          <h2>Known Faces</h2>
          {loading ? (
            <p className="loading">Loading faces...</p>
          ) : (
            <FacesList faces={faces} onRemoveSuccess={handleRemoveSuccess} />
          )}
        </section>

        {systemRunning && (
          <section className="section">
            <h2>📹 Live Detections</h2>
            {reviewPrompt && (
              <div
                style={{
                  marginBottom: '16px',
                  padding: '14px',
                  borderRadius: '10px',
                  backgroundColor: '#fff4e5',
                  border: '1px solid #f0ad4e',
                  color: '#8a5a00',
                }}
              >
                <strong>Do you know this person?</strong>
                <div style={{ marginTop: '6px', marginBottom: '12px' }}>
                  An unknown clear face was detected with medium risk. If you know this person, enroll them below so they become known. Otherwise, keep them as high risk.
                </div>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <button className="start-button" onClick={handleKnownUnknownFace}>
                    Yes, enroll as known
                  </button>
                  <button className="start-button" onClick={handleUnknownUnknownFace}>
                    No, keep as high risk
                  </button>
                </div>
              </div>
            )}
            {detections.length === 0 ? (
              <p style={{ color: '#999', fontStyle: 'italic' }}>No detections yet...</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
                {detections.slice(-10).reverse().map((det, idx) => (
                  (() => {
                    const riskColor = det.risk === 'High' ? '#d9534f' : det.risk === 'Medium' ? '#f0ad4e' : '#5cb85c'
                    const backgroundColor = det.risk === 'High' ? '#ffe0e0' : det.risk === 'Medium' ? '#fff1d6' : '#e0ffe0'
                    const borderColor = det.risk === 'High' ? '#ffcccc' : det.risk === 'Medium' ? '#ffd699' : '#ccffcc'

                    return (
                      <div key={idx} style={{
                        padding: '10px',
                        borderRadius: '6px',
                        backgroundColor,
                        border: `1px solid ${borderColor}`,
                        fontSize: '14px',
                      }}>
                        <strong>{det.name}</strong> {det.name !== 'Unknown' && `| ${det.confidence.toFixed(1)}% match`} | Distance: {det.distance.toFixed(4)} | Risk: <span style={{ color: riskColor, fontWeight: 'bold' }}>{det.risk}</span>
                      </div>
                    )
                  })()
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
