import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, Tooltip } from 'react-leaflet'
import api from '../api'
import { format } from 'date-fns'
import 'leaflet/dist/leaflet.css'

export default function VehicleJourneyPage() {
  const { plate } = useParams()
  const [timeline, setTimeline] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!plate) return
    api.get(`/investigation/timeline/${plate}`)
      .then((r) => setTimeline(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [plate])

  if (loading) return (
    <div className="flex items-center gap-1" style={{ padding: '3rem', justifyContent: 'center' }}>
      <span className="spinner" /><span className="text-muted">Loading journey...</span>
    </div>
  )

  if (!timeline || timeline.total_observations === 0) return (
    <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
      No journey data for <span className="font-mono font-bold">{plate}</span>
    </div>
  )

  const points = timeline.timeline.filter((t) => t.latitude && t.longitude)
  const positions = points.map((t) => [t.latitude, t.longitude])
  const centre = positions.length > 0 ? positions[0] : [22.2587, 71.1924]

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            Vehicle Journey — <span className="font-mono text-cyan">{plate}</span>
          </h1>
          <div className="page-subtitle">Observed CCTV Movement Path</div>
        </div>
        <div className="flex gap-2">
          <span className="text-sm"><b className="text-blue">{timeline.total_observations}</b> <span className="text-muted">observations</span></span>
          <span className="text-sm"><b className="text-cyan">{timeline.cameras_count}</b> <span className="text-muted">cameras</span></span>
        </div>
      </div>

      {/* Journey Timeline */}
      <div className="card mb-2">
        <div className="section-title">Camera Sequence</div>
        <div className="flex" style={{ gap: 0, overflowX: 'auto', paddingBottom: '0.5rem' }}>
          {timeline.timeline.map((entry, i) => (
            <React.Fragment key={i}>
              <div className="glass-card" style={{ minWidth: 180, padding: '0.75rem', flex: '0 0 auto' }}>
                <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.8rem', marginBottom: 4 }}>
                  Step {i + 1}
                </div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{entry.camera_name}</div>
                <div className="text-xs text-muted mt-1">
                  {format(new Date(entry.first_seen), 'HH:mm:ss')} → {format(new Date(entry.last_seen), 'HH:mm:ss')}
                </div>
                {entry.plate_confidence && (
                  <span className={`badge mt-1 ${entry.plate_confidence >= 0.85 ? 'badge-green' : 'badge-yellow'}`}>
                    {(entry.plate_confidence * 100).toFixed(0)}% conf
                  </span>
                )}
                {entry.snapshot_path && (
                  <div className="mt-1">
                    <img src={entry.snapshot_path} alt="snapshot"
                      style={{ width: '100%', borderRadius: 4, maxHeight: 80, objectFit: 'cover', cursor: 'pointer' }}
                      onClick={() => window.open(entry.snapshot_path, '_blank')}
                    />
                  </div>
                )}
              </div>
              {i < timeline.timeline.length - 1 && (
                <div className="flex items-center" style={{ color: 'var(--accent-blue)', fontSize: '1.2rem', padding: '0 0.5rem', flexShrink: 0 }}>→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* GIS Map */}
      {positions.length > 0 && (
        <div className="map-container" style={{ height: '50vh' }}>
          <MapContainer center={centre} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; CARTO'
            />
            {/* Journey polyline */}
            <Polyline positions={positions} pathOptions={{ color: '#3b82f6', weight: 3, dashArray: '8 4' }} />
            {/* Camera markers */}
            {points.map((entry, i) => (
              <CircleMarker
                key={i}
                center={[entry.latitude, entry.longitude]}
                radius={10}
                pathOptions={{ color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 0.9 }}
              >
                <Tooltip permanent>
                  <span style={{ fontWeight: 700, color: '#111' }}>{i + 1}. {entry.camera_name}</span>
                </Tooltip>
                <Popup>
                  <div style={{ color: '#111', minWidth: 160 }}>
                    <b>Step {i + 1}: {entry.camera_name}</b>
                    <div style={{ fontSize: 11, marginTop: 4 }}>
                      <div>First: {format(new Date(entry.first_seen), 'HH:mm:ss')}</div>
                      <div>Last: {format(new Date(entry.last_seen), 'HH:mm:ss')}</div>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      )}

      {positions.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
          No GPS coordinates available for camera locations. Add lat/lon to cameras in the registry.
        </div>
      )}
    </div>
  )
}
