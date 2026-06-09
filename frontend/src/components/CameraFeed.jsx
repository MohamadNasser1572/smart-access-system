import { useState, useEffect, useRef } from 'react'

const POLL_MS = 100 // ~10 fps

function CameraFeed({ systemRunning }) {
  const [blobUrl, setBlobUrl] = useState(null)
  const prevUrlRef = useRef(null)

  useEffect(() => {
    if (!systemRunning) {
      // Clean up any leftover blob URL when system stops.
      if (prevUrlRef.current) {
        URL.revokeObjectURL(prevUrlRef.current)
        prevUrlRef.current = null
      }
      setBlobUrl(null)
      return
    }

    let cancelled = false

    const fetchFrame = async () => {
      try {
        const res = await fetch('/api/frame')
        if (!res.ok || cancelled) return
        const blob = await res.blob()
        if (cancelled) return
        const url = URL.createObjectURL(blob)
        if (prevUrlRef.current) URL.revokeObjectURL(prevUrlRef.current)
        prevUrlRef.current = url
        setBlobUrl(url)
      } catch {
        // backend not ready yet — next tick will retry
      }
    }

    fetchFrame()
    const id = setInterval(fetchFrame, POLL_MS)

    return () => {
      cancelled = true
      clearInterval(id)
      if (prevUrlRef.current) {
        URL.revokeObjectURL(prevUrlRef.current)
        prevUrlRef.current = null
      }
      setBlobUrl(null)
    }
  }, [systemRunning])

  if (!systemRunning) {
    return <p style={{ color: '#999', fontStyle: 'italic' }}>Start the system to view the camera feed.</p>
  }

  return blobUrl ? (
    <img
      src={blobUrl}
      alt="Live camera feed"
      style={{ width: '100%', borderRadius: '8px', display: 'block' }}
    />
  ) : (
    <p style={{ color: '#999', fontStyle: 'italic' }}>Connecting to camera...</p>
  )
}

export default CameraFeed
