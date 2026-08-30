import React, { useEffect, useState } from 'react'
import api from '../api'
import { format } from 'date-fns'

const STATUS_CONFIG = {
  online:       { color: 'var(--accent-green)',  label: 'Online' },
  offline:      { color: 'var(--accent-red)',    label: 'Offline' },
  frozen:       { color: 'var(--accent-orange)', label: 'Frozen' },
  dark:         { color: 'var(--text-muted)',    label: 'Dark' },
  degraded:     { color: 'var(--accent-yellow)', label: 'Degraded' },
  reconnecting: { color: 'var(--accent-cyan)',   label: 'Reconnecting' },
}

function StatusDot({ online }) {
  return (
    <span style={{
      width: 8, height: 8, borderRadius: '50%',
      background: online ? 'var(--accent-green)' : 'var(--accent-red)',
      display: 'inline-block',
    }} />
  )
}

function ScoreBar({ value, max = 1 }) {
  const pct = Math.min(100, ((value ?? 0) / max) * 100)
  const color = pct > 70 ? 'var(--accent-green)' : pct > 40 ? 'var(--accent-yellow)' : 'var(--accent-red)'
  return (
    <div style={{ background: 'var(--bg-glass)', borderRadius: 3, height: 4, width: 80, overflow: 'hidden' }}>
      <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.3s' }} />
    </div>
  )
}

export default function CameraHealthPage() {
  const [healthData, setHealthData] = useState([])
  const [cameras, setCameras] = useState([])

  useEffect(() => {
    api.get('/health').then((r) => setHealthData(r.data)).catch(() => {})
    api.get('/cameras?limit=500').then((r) => setCameras(r.data)).catch(() => {})
    const interval = setInterval(() => {
      api.get('/health').then((r) => setHealthData(r.data)).catch(() => {})
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const getCamName = (id) => cameras.find((c) => c.external_camera_id === id)?.name || id

  const online = healthData.filter((h) => h.online).length
  const offline = healthData.filter((h) => !h.online).length
  const frozen = healthData.filter((h) => h.freeze_status).length
  const dark = healthData.filter((h) => h.is_dark).length

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Camera Health</h1>
          <div className="page-subtitle">Live stream diagnostics</div>
        </div>
        <div className="live-dot" />
      </div>

      {/* Summary */}
      <div className="stat-grid mb-2">
        <div className="stat-card"><div className="stat-label">Online</div><div className="stat-value green">{online}</div></div>
        <div className="stat-card"><div className="stat-label">Offline</div><div className="stat-value red">{offline}</div></div>
        <div className="stat-card"><div className="stat-label">Frozen</div><div className="stat-value orange">{frozen}</div></div>
        <div className="stat-card"><div className="stat-label">Dark</div><div className="stat-value" style={{ color: 'var(--text-muted)' }}>{dark}</div></div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Camera</th>
              <th>AI Worker</th>
              <th>Blur Score</th>
              <th>Brightness</th>
              <th>Latency</th>
              <th>Issues</th>
              <th>Last Check</th>
            </tr>
          </thead>
          <tbody>
            {healthData.map((h) => (
              <tr key={h.camera_id}>
                <td><StatusDot online={h.online} /></td>
                <td style={{ fontWeight: 500 }}>{getCamName(h.camera_id)}</td>
                <td>
                  <span className={`badge ${h.ai_worker_status === 'healthy' ? 'badge-green' : h.ai_worker_status ? 'badge-red' : 'badge-gray'}`}>
                    {h.ai_worker_status || 'unknown'}
                  </span>
                </td>
                <td>
                  <div className="flex items-center gap-1">
                    <ScoreBar value={h.blur_score} max={100} />
                    <span className="text-xs text-muted">{h.blur_score?.toFixed(1) ?? '—'}</span>
                  </div>
                </td>
                <td>
                  <div className="flex items-center gap-1">
                    <ScoreBar value={h.brightness_score} max={255} />
                    <span className="text-xs text-muted">{h.brightness_score?.toFixed(0) ?? '—'}</span>
                  </div>
                </td>
                <td className="text-xs font-mono">{h.latency_ms ? `${h.latency_ms.toFixed(0)}ms` : '—'}</td>
                <td>
                  <div className="flex gap-1" style={{ flexWrap: 'wrap' }}>
                    {h.freeze_status && <span className="badge badge-orange">FROZEN</span>}
                    {h.is_dark && <span className="badge badge-gray">DARK</span>}
                    {h.is_overexposed && <span className="badge badge-yellow">OVEREXP</span>}
                  </div>
                </td>
                <td className="text-xs text-muted">{h.last_checked_at ? format(new Date(h.last_checked_at), 'HH:mm:ss') : '—'}</td>
              </tr>
            ))}
            {healthData.length === 0 && (
              <tr><td colSpan={8} className="text-muted text-sm" style={{ textAlign: 'center', padding: '2rem' }}>
                No health data yet. Health events arrive from Person A's stream worker.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
