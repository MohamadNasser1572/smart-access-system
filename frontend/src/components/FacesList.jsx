import { useState } from 'react'
import './FacesList.css'

const RISKS = ['Low', 'Medium', 'High']

function FacesList({ faces, onRemoveSuccess, onRiskUpdateSuccess }) {
  const [removing, setRemoving] = useState(null)
  const [updatingRisk, setUpdatingRisk] = useState(null) // "Name|Risk" while in flight
  const [error, setError] = useState('')

  const handleRiskChange = async (name, newRisk) => {
    setUpdatingRisk(`${name}|${newRisk}`)
    setError('')
    try {
      const res = await fetch(`/api/faces/${encodeURIComponent(name)}/risk`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ risk_level: newRisk }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Failed to update risk level')
        return
      }
      onRiskUpdateSuccess(name, newRisk)
    } catch (err) {
      setError('Error: ' + err.message)
    } finally {
      setUpdatingRisk(null)
    }
  }

  const handleRemove = async (name) => {
    if (!confirm(`Are you sure you want to remove ${name}?`)) return

    setRemoving(name)
    setError('')
    try {
      const res = await fetch(`/api/faces/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      })
      const data = await res.json()
      if (!res.ok) {
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

            <div className="risk-buttons">
              {RISKS.map((risk) => {
                const isActive = face.risk_level === risk
                const isLoading = updatingRisk === `${face.name}|${risk}`
                return (
                  <button
                    key={risk}
                    className={`btn-risk btn-risk-${risk.toLowerCase()}${isActive ? ' active' : ''}`}
                    onClick={() => handleRiskChange(face.name, risk)}
                    disabled={isActive || !!updatingRisk || !!removing}
                  >
                    {isLoading ? '...' : risk}
                  </button>
                )
              })}
            </div>

            <button
              className="btn-delete"
              onClick={() => handleRemove(face.name)}
              disabled={!!removing || !!updatingRisk}
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
