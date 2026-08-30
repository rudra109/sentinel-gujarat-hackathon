import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import api from '../api'
import 'leaflet/dist/leaflet.css'

const STATUS_COLORS = {
  online: '#22c55e',
  offline: '#ef4444',
  degraded: '#eab308',
  reconnecting: '#f97316',
  unknown: '#64748b',
}

// Alert-aware color
function getCameraColor(cam, alertCameras) {
  if (alertCameras.has(cam.external_camera_id)) return '#ef4444'
  return STATUS_COLORS[cam.live_status] || STATUS_COLORS.unknown
}

export default function GISMap() {
  const [cameras, setCameras] = useState([])
  const [alertCameras, setAlertCameras] = useState(new Set())

  useEffect(() => {
    api.get('/cameras?limit=500').then((r) => setCameras(r.data)).catch(() => {})
    api.get('/alerts?status=OPEN&limit=200').then((r) => {
      const cams = new Set(r.data.map((a) => a.camera_id).filter(Boolean))
      setAlertCameras(cams)
    }).catch(() => {})
  }, [])

  // Gujarat centre
  const centre = [22.2587, 71.1924]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">GIS Camera Map</h1>
          <div className="page-subtitle">Real-time camera status across Gujarat</div>
        </div>
        {/* Legend */}
        <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
          {Object.entries(STATUS_COLORS).map(([s, c]) => (
            <div key={s} className="flex items-center gap-1">
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: c, display: 'inline-block' }} />
              <span className="text-xs text-muted" style={{ textTransform: 'capitalize' }}>{s}</span>
            </div>
          ))}
          <div className="flex items-center gap-1">
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444', display: 'inline-block', boxShadow: '0 0 6px #ef4444' }} />
            <span className="text-xs text-muted">Alert</span>
          </div>
        </div>
      </div>

      <div className="map-container" style={{ height: '70vh' }}>
        <MapContainer
          center={centre}
          zoom={7}
          style={{ height: '100%', width: '100%', background: '#0d1422' }}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com">CARTO</a>'
          />
          {cameras.filter((c) => c.latitude && c.longitude).map((cam) => {
            const color = getCameraColor(cam, alertCameras)
            const hasAlert = alertCameras.has(cam.external_camera_id)
            return (
              <CircleMarker
                key={cam.id}
                center={[cam.latitude, cam.longitude]}
                radius={hasAlert ? 10 : 7}
                pathOptions={{
                  color: color,
                  fillColor: color,
                  fillOpacity: 0.85,
                  weight: hasAlert ? 3 : 1,
                }}
              >
                <Popup>
                  <div style={{ minWidth: 200, color: '#111' }}>
                    <div style={{ fontWeight: 700, marginBottom: 6 }}>{cam.name}</div>
                    <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                      <div><b>ID:</b> {cam.external_camera_id}</div>
                      <div><b>District:</b> {cam.district || '—'}</div>
                      <div><b>Department:</b> {cam.department || '—'}</div>
                      <div><b>Status:</b> {cam.live_status}</div>
                      <div><b>AI:</b> {cam.ai_enabled ? 'Active' : 'Inactive'}</div>
                      {cam.hls_url && (
                        <div style={{ marginTop: 8 }}>
                          <a href={cam.hls_url} target="_blank" rel="noreferrer"
                            style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: 600 }}>
                            ▶ Watch Live
                          </a>
                        </div>
                      )}
                    </div>
                    {hasAlert && (
                      <div style={{ marginTop: 8, background: '#fee2e2', borderRadius: 4, padding: '4px 8px', color: '#ef4444', fontWeight: 600, fontSize: 11 }}>
                        ⚠ ACTIVE ALERT
                      </div>
                    )}
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      <div className="card mt-2">
        <div className="flex" style={{ gap: '2rem' }}>
          <span className="text-sm"><b className="text-blue">{cameras.length}</b> <span className="text-muted">total cameras</span></span>
          <span className="text-sm"><b className="text-green">{cameras.filter((c) => c.live_status === 'online').length}</b> <span className="text-muted">online</span></span>
          <span className="text-sm"><b className="text-red">{cameras.filter((c) => c.live_status === 'offline').length}</b> <span className="text-muted">offline</span></span>
          <span className="text-sm"><b className="text-red">{alertCameras.size}</b> <span className="text-muted">with active alerts</span></span>
        </div>
      </div>
    </div>
  )
}
