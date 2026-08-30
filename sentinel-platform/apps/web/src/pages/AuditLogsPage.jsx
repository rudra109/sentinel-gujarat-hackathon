import React, { useEffect, useState } from 'react'
import api from '../api'
import { format } from 'date-fns'

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([])
  const [action, setAction] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => {
    api.get('/audit', { params: { limit: 200, action: action || undefined } })
      .then((r) => { setLogs(r.data); setLoading(false) })
      .catch(() => setLoading(false))
  }
  useEffect(load, [action])

  const actionBadge = (a) => {
    const color = a.includes('REMOVED') || a.includes('DELETE') ? 'badge-red'
      : a.includes('LOGIN') ? 'badge-blue'
      : a.includes('CREATED') || a.includes('ADDED') ? 'badge-green'
      : a.includes('ACKNOWLEDGED') ? 'badge-cyan'
      : 'badge-gray'
    return <span className={`badge ${color}`}>{a}</span>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Logs</h1>
          <div className="page-subtitle">All sensitive actions are recorded</div>
        </div>
      </div>

      <div className="flex gap-1 mb-2">
        <input id="audit-action-filter" className="input" placeholder="Filter by action..." value={action}
          onChange={(e) => setAction(e.target.value)} style={{ width: 240 }} />
      </div>

      {loading ? (
        <div className="flex items-center gap-1" style={{ padding: '2rem' }}>
          <span className="spinner" /><span className="text-muted">Loading logs...</span>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User ID</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th>IP</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="text-xs font-mono">{format(new Date(log.timestamp), 'dd MMM HH:mm:ss')}</td>
                  <td className="text-xs">{log.user_id ?? '—'}</td>
                  <td>{actionBadge(log.action)}</td>
                  <td className="text-xs text-muted">{log.entity_type ?? '—'}</td>
                  <td className="text-xs font-mono">{log.entity_id ?? '—'}</td>
                  <td className="text-xs font-mono text-muted">{log.ip_address ?? '—'}</td>
                  <td className="text-xs text-muted truncate" style={{ maxWidth: 200 }}>{log.metadata ?? '—'}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={7} className="text-muted text-sm" style={{ textAlign: 'center', padding: '2rem' }}>No audit logs</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
