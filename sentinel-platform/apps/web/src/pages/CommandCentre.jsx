import React, { useEffect, useState } from 'react'
import api from '../api'
import { useAlerts } from '../contexts/AlertsContext'
import { format } from 'date-fns'

export default function CommandCentre() {
  const [stats, setStats] = useState({ total: 0, online: 0, offline: 0, ai_active: 0 })
  const [alertStats, setAlertStats] = useState({ total: 0, open: 0, critical: 0 })
  const [recentDetections, setRecentDetections] = useState([])
  const { alerts: liveAlerts } = useAlerts()

  useEffect(() => {
    api.get('/cameras/stats').then((r) => setStats(r.data)).catch(() => {})
    api.get('/alerts/stats').then((r) => setAlertStats(r.data)).catch(() => {})
    api.get('/detections?limit=10').then((r) => setRecentDetections(r.data)).catch(() => {})
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Command Centre</h1>
          <div className="page-subtitle">Live operational overview</div>
        </div>
        <div className="flex items-center gap-1">
          <span className="live-dot" />
          <span className="text-sm text-muted">Live</span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stat-grid mb-2">
        <div className="stat-card">
          <div className="stat-label">Total Cameras</div>
          <div className="stat-value blue">{stats.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Online</div>
          <div className="stat-value green">{stats.online}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Offline</div>
          <div className="stat-value red">{stats.offline}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">AI Active</div>
          <div className="stat-value cyan">{stats.ai_active}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Open Alerts</div>
          <div className="stat-value yellow" style={alertStats.open > 0 ? { textShadow: '0 0 12px rgba(234,179,8,0.6)' } : {}}>
            {alertStats.open}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Critical</div>
          <div className="stat-value red alert-pulse" style={{ display: 'inline-block' }}>
            {alertStats.critical}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Recent Detections */}
        <div className="card">
          <div className="section-title">Recent ANPR Detections</div>
          {recentDetections.length === 0 ? (
            <div className="text-muted text-sm" style={{ padding: '1rem 0' }}>No recent detections</div>
          ) : (
            <div className="table-wrap" style={{ border: 'none' }}>
              <table>
                <thead>
                  <tr>
                    <th>Plate</th>
                    <th>Camera</th>
                    <th>Confidence</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentDetections.map((d) => (
                    <tr key={d.id}>
                      <td className="plate-number">{d.plate_normalised || d.plate_raw || '—'}</td>
                      <td>{d.camera_id}</td>
                      <td>
                        <span className={`badge ${d.plate_confidence >= 0.85 ? 'badge-green' : d.plate_confidence >= 0.6 ? 'badge-yellow' : 'badge-red'}`}>
                          {d.plate_confidence ? `${(d.plate_confidence * 100).toFixed(0)}%` : '—'}
                        </span>
                      </td>
                      <td className="text-xs">{d.observed_at ? format(new Date(d.observed_at), 'HH:mm:ss') : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Live Alerts Feed */}
        <div className="card">
          <div className="section-title">Live Alert Feed</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: 320, overflowY: 'auto' }}>
            {liveAlerts.length === 0 ? (
              <div className="text-muted text-sm" style={{ padding: '1rem 0' }}>No alerts yet</div>
            ) : (
              liveAlerts.slice(0, 10).map((a, i) => (
                <div key={i} className="glass-card" style={{ padding: '0.75rem', borderLeft: '3px solid var(--accent-red)' }}>
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-red">{a.plate}</span>
                    <span className={`badge ${a.match_type === 'EXACT' ? 'badge-red' : 'badge-orange'}`}>
                      {a.match_type}
                    </span>
                  </div>
                  <div className="text-xs text-muted mt-1">{a.camera_id} · {a.observed_at ? format(new Date(a.observed_at), 'HH:mm:ss') : ''}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* System Health Summary */}
      <div className="card mt-2">
        <div className="section-title">System Status</div>
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
          {[
            { label: 'API', status: 'Operational', color: 'green' },
            { label: 'Event Worker', status: 'Running', color: 'green' },
            { label: 'Database', status: 'Connected', color: 'green' },
            { label: 'Redis', status: 'Connected', color: 'green' },
            { label: 'Evidence Store', status: 'Ready', color: 'green' },
          ].map((s) => (
            <div key={s.label} className="flex items-center gap-1">
              <span className="live-dot" style={{ background: `var(--accent-${s.color})` }} />
              <span className="text-sm">{s.label}</span>
              <span className={`text-xs text-${s.color}`}>{s.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
