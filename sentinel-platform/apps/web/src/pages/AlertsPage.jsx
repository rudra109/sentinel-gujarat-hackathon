import React, { useEffect, useState } from 'react'
import api from '../api'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = () => {
    const params = { limit: 100 }
    if (statusFilter) params.status = statusFilter
    api.get('/alerts', { params }).then((r) => { setAlerts(r.data); setLoading(false) }).catch(() => setLoading(false))
  }

  useEffect(load, [statusFilter])

  const acknowledge = async (id) => {
    const notes = prompt('Acknowledgement notes (optional):') || ''
    await api.post(`/alerts/${id}/acknowledge`, { notes })
    load()
  }

  const severityBadge = (s) => {
    const map = { CRITICAL: 'badge-red', HIGH: 'badge-orange', MEDIUM: 'badge-yellow', LOW: 'badge-gray' }
    return <span className={`badge ${map[s] || 'badge-gray'}`}>{s}</span>
  }
  const statusBadge = (s) => {
    const map = { OPEN: 'badge-red', ACKNOWLEDGED: 'badge-green', CLOSED: 'badge-gray' }
    return <span className={`badge ${map[s] || 'badge-gray'}`}>{s}</span>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Alerts</h1>
          <div className="page-subtitle">{alerts.filter((a) => a.status === 'OPEN').length} open alerts</div>
        </div>
        <div className="flex gap-1">
          {['', 'OPEN', 'ACKNOWLEDGED', 'CLOSED'].map((s) => (
            <button key={s} id={`alert-filter-${s || 'all'}`}
              className={`btn btn-sm ${statusFilter === s ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setStatusFilter(s)}
            >
              {s || 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-1" style={{ padding: '2rem' }}>
          <span className="spinner" /> <span className="text-muted">Loading alerts...</span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {alerts.map((alert) => (
            <div key={alert.id}
              className="glass-card"
              style={{
                borderLeft: `3px solid ${alert.severity === 'CRITICAL' ? 'var(--accent-red)' : alert.severity === 'HIGH' ? 'var(--accent-orange)' : 'var(--accent-yellow)'}`,
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold" style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                    {alert.plate_matched || '—'}
                  </span>
                  {severityBadge(alert.severity)}
                  <span className={`badge ${alert.match_type === 'EXACT' ? 'badge-red' : 'badge-orange'}`}>
                    {alert.match_type}
                  </span>
                  {statusBadge(alert.status)}
                </div>
                <div className="flex gap-1">
                  <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/investigation?plate=${alert.plate_matched}`)}>
                    🔍 Investigate
                  </button>
                  {alert.status === 'OPEN' && (
                    <button id={`ack-alert-${alert.id}`} className="btn btn-primary btn-sm" onClick={() => acknowledge(alert.id)}>
                      ✓ Acknowledge
                    </button>
                  )}
                </div>
              </div>

              <div className="flex gap-3 mt-1" style={{ flexWrap: 'wrap' }}>
                <span className="text-xs text-muted">📷 {alert.camera_id}</span>
                <span className="text-xs text-muted">🕐 {alert.created_at ? format(new Date(alert.created_at), 'dd MMM yyyy HH:mm:ss') : '—'}</span>
                {alert.notes && <span className="text-xs text-muted">📝 {alert.notes}</span>}
              </div>
            </div>
          ))}
          {alerts.length === 0 && (
            <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              No alerts found
            </div>
          )}
        </div>
      )}
    </div>
  )
}
