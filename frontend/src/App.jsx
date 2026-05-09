import { useState, useEffect } from 'react'
import EnrollmentForm from './components/EnrollmentForm'
import FacesList from './components/FacesList'
import './App.css'

function App() {
  const [faces, setFaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [systemRunning, setSystemRunning] = useState(false)

  const fetchFaces = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/faces')
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
      const res = await fetch('http://127.0.0.1:8000/status')
      const data = await res.json()
      setSystemRunning(Boolean(data.system_running))
    } catch (err) {
      console.error('Failed to fetch status', err)
    }
  }

  useEffect(() => {
    fetchFaces()
    fetchStatus()
  }, [])

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
      const res = await fetch('http://127.0.0.1:8000/system/start', { method: 'POST' })
      const data = await res.json()
      if (data.status === 'started' || data.status === 'already_running') {
        setSystemRunning(true)
        setMessage('System started')
        setTimeout(() => setMessage(''), 2500)
      }
    } catch (err) {
      console.error('Failed to start system', err)
      setMessage('Failed to start system')
    }
  }

  const stopSystem = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/system/stop', { method: 'POST' })
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
            <FacesList faces={faces} onRemoveSuccess={handleRemoveSuccess} />
          )}
        </section>
      </main>
    </div>
  )
}

export default App
