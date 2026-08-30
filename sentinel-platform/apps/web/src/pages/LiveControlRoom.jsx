import React, { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import api from '../api'
import { useAlerts } from '../contexts/AlertsContext'

const GRID_OPTIONS = [
  { label: '2×2', value: 4, cls: 'grid-4' },
  { label: '3×3', value: 9, cls: 'grid-9' },
  { label: '4×4', value: 16, cls: 'grid-16' },
]

function CameraCell({ camera, hasAlert }) {
  const videoRef = useRef(null)
  const hlsRef = useRef(null)

  useEffect(() => {
    if (!camera?.hls_url || !videoRef.current) return
    if (Hls.isSupported()) {
      const hls = new Hls({ maxBufferLength: 5, maxMaxBufferLength: 10 })
      hlsRef.current = hls
      hls.loadSource(camera.hls_url)
      hls.attachMedia(videoRef.current)
      hls.on(Hls.Events.MANIFEST_PARSED, () => videoRef.current?.play().catch(() => {}))
    } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
      videoRef.current.src = camera.hls_url
      videoRef.current.play().catch(() => {})
    }
    return () => { hlsRef.current?.destroy() }
  }, [camera?.hls_url])

  return (
    <div className={`camera-cell ${hasAlert ? 'alert-pulse' : ''}`} style={hasAlert ? { borderColor: 'var(--accent-red)' } : {}}>
      {camera?.hls_url ? (
        <video ref={videoRef} muted playsInline style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      ) : (
        <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#080c14', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          {camera ? 'No Stream URL' : 'Select Camera'}
        </div>
      )}

      {camera && (
        <>
          <div className="camera-overlay-top">
            <div className="flex items-center justify-between">
              <span className="camera-name">{camera.name}</span>
              {camera.ai_enabled && (
                <span style={{ background: 'rgba(59,130,246,0.8)', color: '#fff', fontSize: '0.6rem', padding: '1px 5px', borderRadius: 3, fontWeight: 700 }}>AI</span>
              )}
            </div>
          </div>
          <div className="camera-overlay">
            <span className="camera-name" style={{ fontSize: '0.65rem' }}>
              {camera.external_camera_id}
            </span>
            {hasAlert && <span className="camera-alert-badge">ALERT</span>}
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: camera.live_status === 'online' ? 'var(--accent-green)' : 'var(--accent-red)', display: 'inline-block' }} />
          </div>
        </>
      )}
    </div>
  )
}

export default function LiveControlRoom() {
  const [cameras, setCameras] = useState([])
  const [selected, setSelected] = useState([])
  const [gridSize, setGridSize] = useState(4)
  const [gridCls, setGridCls] = useState('grid-4')
  const { alerts } = useAlerts()

  const alertCameraIds = new Set(alerts.map((a) => a.camera_id).filter(Boolean))

  useEffect(() => {
    api.get('/cameras?limit=200').then((r) => {
      const cams = r.data
      setCameras(cams)
      setSelected(cams.slice(0, 4).map((c) => c.id))
    }).catch(() => {})
  }, [])

  const handleGridChange = (opt) => {
    setGridSize(opt.value)
    setGridCls(opt.cls)
    setSelected(cameras.slice(0, opt.value).map((c) => c.id))
  }

  const selectedCameras = selected.map((id) => cameras.find((c) => c.id === id) || null)
  while (selectedCameras.length < gridSize) selectedCameras.push(null)

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Control Room</h1>
          <div className="page-subtitle">Multi-camera live view with AI overlay</div>
        </div>
        <div className="flex gap-1">
          {GRID_OPTIONS.map((opt) => (
            <button key={opt.value} id={`grid-${opt.label}`}
              className={`btn btn-sm ${gridSize === opt.value ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => handleGridChange(opt)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Camera selector */}
      <div className="card mb-2" style={{ padding: '0.75rem' }}>
        <div className="section-title" style={{ marginBottom: '0.5rem' }}>Select Cameras</div>
        <div className="flex gap-1" style={{ flexWrap: 'wrap' }}>
          {cameras.slice(0, 30).map((cam) => {
            const isSelected = selected.includes(cam.id)
            return (
              <button key={cam.id}
                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-ghost'}`}
                style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}
                onClick={() => {
                  if (isSelected) {
                    setSelected(selected.filter((id) => id !== cam.id))
                  } else if (selected.length < gridSize) {
                    setSelected([...selected, cam.id])
                  }
                }}
              >
                {alertCameraIds.has(cam.external_camera_id) && '🔴 '}
                {cam.external_camera_id}
              </button>
            )
          })}
        </div>
      </div>

      {/* Camera Grid */}
      <div className={`camera-grid ${gridCls}`}>
        {selectedCameras.slice(0, gridSize).map((cam, i) => (
          <CameraCell key={i} camera={cam} hasAlert={cam && alertCameraIds.has(cam.external_camera_id)} />
        ))}
      </div>

      {/* Live detections ticker */}
      {alerts.length > 0 && (
        <div className="card mt-2" style={{ borderColor: 'rgba(239,68,68,0.3)', padding: '0.75rem' }}>
          <div className="flex items-center gap-1">
            <span className="live-dot" style={{ background: 'var(--accent-red)' }} />
            <span className="text-sm font-bold text-red">WATCHLIST ALERT</span>
            <span className="font-mono font-bold" style={{ color: 'var(--accent-red)', marginLeft: '0.5rem' }}>{alerts[0].plate}</span>
            <span className="text-xs text-muted">detected at {alerts[0].camera_id}</span>
            <span className={`badge ${alerts[0].match_type === 'EXACT' ? 'badge-red' : 'badge-orange'}`}>{alerts[0].match_type}</span>
          </div>
        </div>
      )}
    </div>
  )
}
