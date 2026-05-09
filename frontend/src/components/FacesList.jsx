import { useState } from 'react'
import './FacesList.css'

function FacesList({ faces, onRemoveSuccess }) {
  const [removing, setRemoving] = useState(null)
  const [error, setError] = useState('')

  const handleRemove = async (name) => {
    if (!confirm(`Are you sure you want to remove ${name}?`)) {
      return
    }

    setRemoving(name)
    setError('')

    try {
      const response = await fetch(`http://127.0.0.1:8000/faces/${name}`, {
        method: 'DELETE',
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Failed to remove face')
        return
      }

      onRemoveSuccess()
    } catch (err) {
      setError('Error: ' + err.message)
    } finally {
      setRemoving(null)
    }
  }

  if (faces.length === 0) {
    return (
      <div className="empty-state">
        <p>No known faces yet. Add one to get started!</p>
      </div>
    )
  }

  return (
    <div className="faces-list">
      {error && <div className="error-message">{error}</div>}
      <div className="faces-grid">
        {faces.map((face) => (
          <div key={face.name} className="face-card">
            <div className="face-header">
              <h3>{face.name}</h3>
              <span className={`risk-badge risk-${face.risk_level.toLowerCase()}`}>
                {face.risk_level}
              </span>
            </div>
            <button
              className="btn-delete"
              onClick={() => handleRemove(face.name)}
              disabled={removing === face.name}
            >
              {removing === face.name ? 'Removing...' : '🗑️ Remove'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FacesList
