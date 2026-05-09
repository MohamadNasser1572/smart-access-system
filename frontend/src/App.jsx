import { useState, useEffect } from 'react'
import EnrollmentForm from './components/EnrollmentForm'
import FacesList from './components/FacesList'
import './App.css'

function App() {
  const [faces, setFaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

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

  useEffect(() => {
    fetchFaces()
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

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Smart Access System</h1>
        <p>Face Enrollment Manager</p>
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
