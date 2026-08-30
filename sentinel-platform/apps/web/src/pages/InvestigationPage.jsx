import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api'
import { format } from 'date-fns'

export default function InvestigationPage() {
  const [searchParams] = useSearchParams()
  const [plate, setPlate] = useState(searchParams.get('plate') || '')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const navigate = useNavigate()

  const doSearch = async (e) => {
    e?.preventDefault()
    if (!plate.trim()) return
    setSearching(true)
    try {
      const r = await api.get('/detections', { params: { plate: plate.trim().toUpperCase(), limit: 100 } })
      setResults(r.data)
    } finally {
      setSearching(false)
    }
  }

  // Auto-search if plate comes from URL param
  React.useEffect(() => { if (plate) doSearch() }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Vehicle Investigation</h1>
          <div className="page-subtitle">Search by plate number</div>
        </div>
        {plate && results.length > 0 && (
          <button className="btn btn-primary btn-sm" onClick={() => navigate(`/journey/${plate.toUpperCase()}`)}>
            🗺 View Journey Map
          </button>
        )}
      </div>

      {/* Search */}
      <form onSubmit={doSearch} className="flex gap-1 mb-2">
        <input
          id="investigation-plate-input"
          className="input font-mono"
          placeholder="GJ05AB1234"
          value={plate}
          onChange={(e) => setPlate(e.target.value.toUpperCase())}
          style={{ width: 240, fontSize: '1.1rem', letterSpacing: '0.08em' }}
        />
        <button id="investigation-search-btn" type="submit" className="btn btn-primary" disabled={searching}>
          {searching ? <span className="spinner" style={{ width: 16, height: 16 }} /> : '🔍 Search'}
        </button>
      </form>

      {/* Results Summary */}
      {results.length > 0 && (
        <div className="stat-grid mb-2">
          <div className="stat-card">
            <div className="stat-label">Total Observations</div>
            <div className="stat-value blue">{results.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Cameras</div>
            <div className="stat-value cyan">{new Set(results.map((r) => r.camera_id)).size}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">First Seen</div>
            <div className="stat-value" style={{ fontSize: '0.9rem' }}>
              {format(new Date(results[results.length - 1].observed_at), 'dd MMM HH:mm')}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Last Seen</div>
            <div className="stat-value" style={{ fontSize: '0.9rem' }}>
              {format(new Date(results[0].observed_at), 'dd MMM HH:mm')}
            </div>
          </div>
        </div>
      )}

      {/* Observations Table */}
      {results.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Plate</th>
                <th>Camera</th>
                <th>Vehicle Type</th>
                <th>Confidence</th>
                <th>Observed At</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {results.map((obs) => (
                <tr key={obs.id}>
                  <td className="plate-number">{obs.plate_normalised || obs.plate_raw || '—'}</td>
                  <td>{obs.camera_id}</td>
                  <td className="text-xs">{obs.vehicle_type || '—'}</td>
                  <td>
                    {obs.plate_confidence ? (
                      <span className={`badge ${obs.plate_confidence >= 0.85 ? 'badge-green' : obs.plate_confidence >= 0.6 ? 'badge-yellow' : 'badge-red'}`}>
                        {(obs.plate_confidence * 100).toFixed(0)}%
                      </span>
                    ) : '—'}
                  </td>
                  <td className="text-xs">{format(new Date(obs.observed_at), 'dd MMM yyyy HH:mm:ss')}</td>
                  <td>
                    <div className="flex gap-1">
                      {obs.snapshot_path && (
                        <a href={obs.snapshot_path} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">📷</a>
                      )}
                      {obs.plate_crop_path && (
                        <a href={obs.plate_crop_path} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">🔲</a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {results.length === 0 && plate && !searching && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          No observations found for <span className="font-mono font-bold">{plate}</span>
        </div>
      )}
    </div>
  )
}
