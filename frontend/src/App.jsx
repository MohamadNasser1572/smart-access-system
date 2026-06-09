import { useState, useEffect, useRef } from 'react'
import EnrollmentForm from './components/EnrollmentForm'
import FacesList from './components/FacesList'
import CameraFeed from './components/CameraFeed'
import './App.css'

function App() {
  const API_BASE = '/api'
  const reviewedPromptKeyRef = useRef('')
  const lastNotifiedRef = useRef({})
  const unknownFirstSeenRef = useRef(null) // timestamp when unknown first appeared continuously

  const [faces, setFaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [systemRunning, setSystemRunning] = useState(false)
  const [detections, setDetections] = useState([])
  const [reviewPrompt, setReviewPrompt] = useState(null)

  // Inline quick-enroll form state (shown inside the "Do you know this person?" prompt)
  const [inlineEnrolling, setInlineEnrolling] = useState(false)
  const inlineEnrollingRef = useRef(false) // ref copy so fetchDetections closure can read it
  const [inlineName, setInlineName] = useState('')
  const [inlineRisk, setInlineRisk] = useState('Low')
  const [inlineError, setInlineError] = useState('')
  const [inlineLoading, setInlineLoading] = useState(false)
  // Blob captured at the moment the user clicks "Yes" — frozen so new detections can't overwrite it.
  const capturedFaceBlobRef = useRef(null)
  const [capturedFaceUrl, setCapturedFaceUrl] = useState(null)

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

      if (Notification.permission === 'granted') {
        const now = Date.now()
        nextDetections.forEach((det) => {
          if (det.risk === 'High') {
            const last = lastNotifiedRef.current[det.name] || 0
            if (now - last > 30000) {
              new Notification('High Risk Detected', {
                body: det.name === 'Unknown' ? 'Unknown person detected' : `${det.name} flagged as High risk`,
                tag: det.name,
              })
              lastNotifiedRef.current[det.name] = now
            }
          } else {
            delete lastNotifiedRef.current[det.name]
          }
        })
      }

      const mediumUnknown = nextDetections.find(
        (det) => det.name === 'Unknown' && String(det.risk).toLowerCase() === 'medium',
      )

      if (mediumUnknown) {
        // Start the continuous-presence timer on first detection.
        if (!unknownFirstSeenRef.current) {
          unknownFirstSeenRef.current = Date.now()
        }
        // Only show the prompt after the unknown has been on screen for 4 seconds
        // so brief occlusions or quick movements don't trigger it.
        const elapsed = Date.now() - unknownFirstSeenRef.current
        if (elapsed >= 4000) {
          const promptKey = `${mediumUnknown.name}|${mediumUnknown.risk}`
          if (reviewedPromptKeyRef.current !== promptKey) {
            setReviewPrompt({ ...mediumUnknown, promptKey })
            if (!inlineEnrollingRef.current) {
              setInlineEnrolling(false)
              setInlineName('')
              setInlineRisk('Low')
              setInlineError('')
            }
          }
        }
      } else {
        // Unknown left the frame — reset the timer and auto-dismiss the prompt
        // (unless the operator is mid-way through filling the enroll form).
        unknownFirstSeenRef.current = null
        reviewedPromptKeyRef.current = ''
        if (!inlineEnrollingRef.current) {
          setReviewPrompt(null)
        }
      }
    } catch (err) {
      console.error('Failed to fetch detections', err)
    }
  }

  const dismissPrompt = (nextMessage) => {
    // Clear the reviewed key so the prompt can reappear if a new unknown
    // is detected later in the same session (e.g. after re-enrollment).
    reviewedPromptKeyRef.current = ''
    setReviewPrompt(null)
    inlineEnrollingRef.current = false
    setInlineEnrolling(false)
    setInlineName('')
    setInlineRisk('Low')
    setInlineError('')
    if (capturedFaceUrl) {
      URL.revokeObjectURL(capturedFaceUrl)
      setCapturedFaceUrl(null)
      capturedFaceBlobRef.current = null
    }
    if (nextMessage) {
      setMessage(nextMessage)
      setTimeout(() => setMessage(''), 4000)
    }
  }

  // Called when the user clicks "Yes, enroll them" — captures the face image
  // immediately into a local blob so new detections can't overwrite it.
  const handleYesEnroll = async () => {
    try {
      const res = await fetch(`${API_BASE}/unknown-face`)
      if (res.ok) {
        const blob = await res.blob()
        capturedFaceBlobRef.current = blob
        setCapturedFaceUrl(URL.createObjectURL(blob))
      }
    } catch {
      // If fetch fails we'll show an error on submit instead.
    }
    inlineEnrollingRef.current = true
    setInlineEnrolling(true)
  }

  const handleInlineEnroll = async (e) => {
    e.preventDefault()
    if (!inlineName.trim()) {
      setInlineError('Please enter a name')
      return
    }
    if (!capturedFaceBlobRef.current) {
      setInlineError('Face image not available — try again')
      return
    }

    setInlineLoading(true)
    setInlineError('')

    try {
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onloadend = () => resolve(reader.result.split(',')[1])
        reader.onerror = () => reject(new Error('Failed to read image'))
        reader.readAsDataURL(capturedFaceBlobRef.current)
      })

      const res = await fetch(`${API_BASE}/faces/enroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: inlineName.trim(),
          risk_level: inlineRisk,
          photo_base64: base64,
        }),
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Enrollment failed')

      // Reload known faces so the running system recognises the person immediately.
      try {
        await fetch(`${API_BASE}/reload-faces`, { method: 'POST' })
      } catch {
        // Non-fatal — recognition will update on next system restart.
      }

      fetchFaces()
      dismissPrompt(`${inlineName.trim()} enrolled — now recognised!`)
    } catch (err) {
      setInlineError(err.message || 'Enrollment failed')
    } finally {
      setInlineLoading(false)
    }
  }

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  useEffect(() => {
    fetchFaces()
    fetchStatus()

    const interval = setInterval(() => {
      fetchStatus()
    }, 2000)

    const detectionInterval = setInterval(() => {
      if (systemRunning) {
        fetchDetections()
      }
    }, 2000)

    return () => {
      clearInterval(interval)
      clearInterval(detectionInterval)
    }
  }, [systemRunning])

  const handleEnrollSuccess = async () => {
    setMessage('Enrolled! Updating recognition...')
    try {
      await fetch(`${API_BASE}/reload-faces`, { method: 'POST' })
      setMessage('Face enrolled — recognition updated!')
    } catch {
      setMessage('Face enrolled (restart may be needed for recognition to update)')
    }
    fetchFaces()
    setTimeout(() => setMessage(''), 4000)
  }

  const handleRemoveSuccess = async () => {
    setMessage('Face removed successfully!')
    try {
      await fetch(`${API_BASE}/reload-faces`, { method: 'POST' })
    } catch {
      // Non-fatal — recognition will update on next system restart.
    }
    fetchFaces()
    setTimeout(() => setMessage(''), 3000)
  }

  const handleRiskUpdateSuccess = (name, newRisk) => {
    setMessage(`${name} set to ${newRisk} risk`)
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
        <section className="section">
          <h2>Enroll New Face</h2>
          <EnrollmentForm onSuccess={handleEnrollSuccess} />
        </section>

        <section className="section">
          <h2>Known Faces</h2>
          {loading ? (
            <p className="loading">Loading faces...</p>
          ) : (
            <FacesList faces={faces} onRemoveSuccess={handleRemoveSuccess} onRiskUpdateSuccess={handleRiskUpdateSuccess} />
          )}
        </section>

        <section className="section">
          <h2>📹 Live Detections</h2>

          {!systemRunning ? (
            <p style={{ color: '#999', fontStyle: 'italic' }}>Start the system to see detections.</p>
          ) : (<>

            {reviewPrompt && (
              <div style={{
                marginBottom: '16px',
                padding: '16px',
                borderRadius: '10px',
                backgroundColor: '#fff4e5',
                border: '1px solid #f0ad4e',
                color: '#8a5a00',
              }}>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
                  <img
                    src={capturedFaceUrl || `/api/unknown-face?t=${reviewPrompt.promptKey}`}
                    alt="Unknown face"
                    style={{ width: '90px', height: '90px', objectFit: 'cover', borderRadius: '6px', flexShrink: 0 }}
                    onError={(e) => { e.currentTarget.style.display = 'none' }}
                  />
                  <div style={{ flex: 1 }}>
                    <strong style={{ fontSize: '15px' }}>Do you know this person?</strong>

                    {!inlineEnrolling ? (
                      <>
                        <p style={{ margin: '6px 0 12px' }}>
                          An unknown face was detected. Enroll them now or dismiss.
                        </p>
                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                          <button
                            className="start-button"
                            onClick={handleYesEnroll}
                          >
                            Yes, enroll them
                          </button>
                          <button
                            className="start-button"
                            style={{ backgroundColor: '#888' }}
                            onClick={() => dismissPrompt('Unknown face dismissed.')}
                          >
                            No, dismiss
                          </button>
                        </div>
                      </>
                    ) : (
                      <form onSubmit={handleInlineEnroll} style={{ marginTop: '10px' }}>
                        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Name</label>
                            <input
                              type="text"
                              value={inlineName}
                              onChange={(e) => setInlineName(e.target.value)}
                              placeholder="Enter name"
                              disabled={inlineLoading}
                              autoFocus
                              style={{
                                padding: '6px 10px',
                                borderRadius: '6px',
                                border: '1px solid #f0ad4e',
                                fontSize: '14px',
                                minWidth: '160px',
                              }}
                            />
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Risk Level</label>
                            <select
                              value={inlineRisk}
                              onChange={(e) => setInlineRisk(e.target.value)}
                              disabled={inlineLoading}
                              style={{
                                padding: '6px 10px',
                                borderRadius: '6px',
                                border: '1px solid #f0ad4e',
                                fontSize: '14px',
                                backgroundColor: '#fff',
                              }}
                            >
                              <option value="Low">Low (Trusted)</option>
                              <option value="Medium">Medium (Caution)</option>
                              <option value="High">High (Restricted)</option>
                            </select>
                          </div>
                          <button
                            type="submit"
                            className="start-button"
                            disabled={inlineLoading || !inlineName.trim()}
                            style={{ alignSelf: 'flex-end' }}
                          >
                            {inlineLoading ? 'Enrolling...' : 'Enroll'}
                          </button>
                          <button
                            type="button"
                            className="start-button"
                            style={{ backgroundColor: '#888', alignSelf: 'flex-end' }}
                            disabled={inlineLoading}
                            onClick={() => {
                              inlineEnrollingRef.current = false
                              setInlineEnrolling(false)
                              setInlineError('')
                              if (capturedFaceUrl) {
                                URL.revokeObjectURL(capturedFaceUrl)
                                setCapturedFaceUrl(null)
                                capturedFaceBlobRef.current = null
                              }
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                        {inlineError && (
                          <p style={{ color: '#c0392b', marginTop: '8px', fontSize: '13px' }}>{inlineError}</p>
                        )}
                      </form>
                    )}
                  </div>
                </div>
              </div>
            )}

            {detections.length === 0 ? (
              <p style={{ color: '#999', fontStyle: 'italic' }}>No detections yet...</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {detections.map((det) => {
                  const isKnown = det.name !== 'Unknown'
                  const lowConfidence = isKnown && Number(det.confidence) < 20
                  const effectiveRisk = lowConfidence ? 'Medium' : det.risk
                  const riskColor = effectiveRisk === 'High' ? '#d9534f' : effectiveRisk === 'Medium' ? '#f0ad4e' : '#5cb85c'
                  const backgroundColor = effectiveRisk === 'High' ? '#ffe0e0' : effectiveRisk === 'Medium' ? '#fff1d6' : '#e0ffe0'
                  const borderColor = effectiveRisk === 'High' ? '#ffcccc' : effectiveRisk === 'Medium' ? '#ffd699' : '#ccffcc'

                  return (
                    <div key={det.name} style={{
                      padding: '14px 16px',
                      borderRadius: '8px',
                      backgroundColor,
                      border: `1px solid ${borderColor}`,
                      fontSize: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '16px',
                      flexWrap: 'wrap',
                    }}>
                      <span style={{ fontWeight: 'bold', fontSize: '15px', minWidth: '120px' }}>
                        {det.name}
                      </span>
                      {isKnown && (
                        <span style={{ color: '#555' }}>
                          Accuracy:{' '}
                          <strong style={{ color: lowConfidence ? '#f0ad4e' : 'inherit' }}>
                            {Number(det.confidence).toFixed(1)}%
                          </strong>
                          {lowConfidence && (
                            <span style={{ marginLeft: '6px', color: '#f0ad4e', fontSize: '12px' }}>
                              (low confidence)
                            </span>
                          )}
                        </span>
                      )}
                      <span style={{ color: '#555' }}>
                        Distance: <strong>{Number(det.distance).toFixed(4)}</strong>
                      </span>
                      <span style={{ marginLeft: 'auto', fontWeight: 'bold', color: riskColor, fontSize: '15px' }}>
                        {effectiveRisk} Risk
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </>)}
        </section>

        <section className="section">
          <h2>🎥 Camera Feed</h2>
          <CameraFeed systemRunning={systemRunning} />
        </section>
      </main>
    </div>
  )
}

export default App
