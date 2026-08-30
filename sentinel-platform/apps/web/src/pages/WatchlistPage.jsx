import React, { useEffect, useState } from 'react'
import api from '../api'
import { format } from 'date-fns'

const CATEGORIES = ['investigation', 'stolen', 'suspect', 'blacklisted', 'test-target']
const PRIORITIES = [{ v: 1, label: 'Critical' }, { v: 2, label: 'High' }, { v: 3, label: 'Medium' }, { v: 4, label: 'Low' }]

export default function WatchlistPage() {
  const [entries, setEntries] = useState([])
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ plate_number: '', category: 'investigation', priority: 2, reason: '', expires_at: '' })
  const [loading, setLoading] = useState(false)

  const load = () => {
    api.get('/watchlist', { params: { active_only: true, search: search || undefined } })
      .then((r) => setEntries(r.data)).catch(() => {})
  }
  useEffect(load, [search])

  const handleAdd = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/watchlist', {
        ...form,
        priority: parseInt(form.priority),
        expires_at: form.expires_at || null,
      })
      setShowForm(false)
      setForm({ plate_number: '', category: 'investigation', priority: 2, reason: '', expires_at: '' })
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add')
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (id, plate) => {
    if (!confirm(`Deactivate watchlist entry for ${plate}?`)) return
    await api.delete(`/watchlist/${id}`)
    load()
  }

  const catBadge = (c) => {
    const map = { stolen: 'badge-red', suspect: 'badge-orange', investigation: 'badge-blue', blacklisted: 'badge-purple', 'test-target': 'badge-yellow' }
    return <span className={`badge ${map[c] || 'badge-gray'}`}>{c}</span>
  }

  const priLabel = (p) => PRIORITIES.find((x) => x.v === p)?.label || p

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Watchlist</h1>
          <div className="page-subtitle">{entries.length} active entries</div>
        </div>
        <button id="btn-add-watchlist" className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
          + Add Plate
        </button>
      </div>

      {/* Add Form */}
      {showForm && (
        <div className="card mb-2">
          <div className="section-title">Add to Watchlist</div>
          <form onSubmit={handleAdd}>
            <div className="grid-3" style={{ gap: '0.75rem' }}>
              <div className="form-group">
                <label className="form-label">Plate Number *</label>
                <input id="watchlist-plate" className="input font-mono" placeholder="GJ05AB1234"
                  value={form.plate_number} onChange={(e) => setForm({ ...form, plate_number: e.target.value.toUpperCase() })} required />
              </div>
              <div className="form-group">
                <label className="form-label">Category *</label>
                <select id="watchlist-category" className="select" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Priority *</label>
                <select id="watchlist-priority" className="select" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                  {PRIORITIES.map((p) => <option key={p.v} value={p.v}>{p.label}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label className="form-label">Reason</label>
                <input className="input" placeholder="Brief reason for watchlisting..." value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
              </div>
              <div className="form-group">
                <label className="form-label">Expires At (optional)</label>
                <input type="datetime-local" className="input" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })} />
              </div>
            </div>
            <div className="flex gap-1 mt-2">
              <button id="watchlist-submit" type="submit" className="btn btn-primary btn-sm" disabled={loading}>
                {loading ? 'Adding...' : 'Add to Watchlist'}
              </button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="mb-2">
        <input id="watchlist-search" className="input" placeholder="Search plate..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }} />
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Plate Number</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Reason</th>
              <th>Added</th>
              <th>Expires</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id}>
                <td className="plate-number">{e.plate_number}</td>
                <td>{catBadge(e.category)}</td>
                <td>
                  <span className={`badge ${e.priority === 1 ? 'badge-red' : e.priority === 2 ? 'badge-orange' : 'badge-gray'}`}>
                    {priLabel(e.priority)}
                  </span>
                </td>
                <td className="text-xs text-muted truncate" style={{ maxWidth: 200 }}>{e.reason || '—'}</td>
                <td className="text-xs">{format(new Date(e.created_at), 'dd MMM HH:mm')}</td>
                <td className="text-xs">{e.expires_at ? format(new Date(e.expires_at), 'dd MMM yyyy') : '—'}</td>
                <td>
                  <button className="btn btn-danger btn-sm" onClick={() => handleRemove(e.id, e.plate_number)}>Remove</button>
                </td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr><td colSpan={7} className="text-muted text-sm" style={{ textAlign: 'center', padding: '2rem' }}>No watchlist entries</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
