import React, { useEffect, useState } from 'react'
import api from '../api'
import { format } from 'date-fns'

export default function CameraRegistry() {
  const [cameras, setCameras] = useState([])
  const [stats, setStats] = useState({})
  const [search, setSearch] = useState('')
  const [district, setDistrict] = useState('')
  const [status, setStatus] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [newCam, setNewCam] = useState({ external_camera_id: '', name: '', rtsp_url: '', hls_url: '', latitude: '', longitude: '', district: '', department: '' })

  const loadCameras = () => {
    const params = {}
    if (search) params.search = search
    if (district) params.district = district
    if (status) params.status = status
    api.get('/cameras', { params }).then((r) => setCameras(r.data)).catch(() => {})
  }

  useEffect(() => {
    loadCameras()
    api.get('/cameras/stats').then((r) => setStats(r.data)).catch(() => {})
  }, [search, district, status])

  const handleSync = async () => {
    setSyncing(true)
    try {
      await api.post('/cameras/sync')
      setTimeout(() => { loadCameras(); setSyncing(false) }, 2000)
    } catch { setSyncing(false) }
  }

  const handleAddCamera = async (e) => {
    e.preventDefault()
    try {
      await api.post('/cameras', {
        ...newCam,
        latitude: newCam.latitude ? parseFloat(newCam.latitude) : null,
        longitude: newCam.longitude ? parseFloat(newCam.longitude) : null,
      })
      setShowAdd(false)
      loadCameras()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add camera')
    }
  }

  const toggleAI = async (cam) => {
    await api.patch(`/cameras/${cam.id}`, { ai_enabled: !cam.ai_enabled })
    loadCameras()
  }

  const statusBadge = (s) => {
    const map = { online: 'badge-green', offline: 'badge-red', degraded: 'badge-yellow', reconnecting: 'badge-orange', unknown: 'badge-gray' }
    return <span className={`badge ${map[s] || 'badge-gray'}`}>{s}</span>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Camera Registry</h1>
          <div className="page-subtitle">{stats.total || 0} cameras · {stats.online || 0} online</div>
        </div>
        <div className="flex gap-1">
          <button id="btn-add-camera" className="btn btn-ghost btn-sm" onClick={() => setShowAdd(!showAdd)}>+ Add Camera</button>
          <button id="btn-sync-cameras" className="btn btn-primary btn-sm" onClick={handleSync} disabled={syncing}>
            {syncing ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '⟳'} Sync from Sandbox
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-1 mb-2" style={{ flexWrap: 'wrap' }}>
        <input id="camera-search" className="input" placeholder="Search cameras..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 220 }} />
        <input id="camera-district" className="input" placeholder="District..." value={district} onChange={(e) => setDistrict(e.target.value)} style={{ width: 160 }} />
        <select id="camera-status-filter" className="select" value={status} onChange={(e) => setStatus(e.target.value)} style={{ width: 160 }}>
          <option value="">All Status</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="degraded">Degraded</option>
        </select>
      </div>

      {/* Add Camera Form */}
      {showAdd && (
        <div className="card mb-2">
          <div className="section-title">Add Camera Manually</div>
          <form onSubmit={handleAddCamera}>
            <div className="grid-3" style={{ gap: '0.75rem' }}>
              {[
                { key: 'external_camera_id', label: 'Camera ID', required: true },
                { key: 'name', label: 'Name', required: true },
                { key: 'rtsp_url', label: 'RTSP URL' },
                { key: 'hls_url', label: 'HLS URL' },
                { key: 'latitude', label: 'Latitude' },
                { key: 'longitude', label: 'Longitude' },
                { key: 'district', label: 'District' },
                { key: 'department', label: 'Department' },
              ].map(({ key, label, required }) => (
                <div key={key} className="form-group">
                  <label className="form-label">{label}{required && ' *'}</label>
                  <input className="input" value={newCam[key]} onChange={(e) => setNewCam({ ...newCam, [key]: e.target.value })} required={required} />
                </div>
              ))}
            </div>
            <div className="flex gap-1 mt-2">
              <button type="submit" className="btn btn-primary btn-sm">Add Camera</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowAdd(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Camera ID</th>
              <th>Name</th>
              <th>District</th>
              <th>Department</th>
              <th>Status</th>
              <th>AI</th>
              <th>Coords</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((cam) => (
              <tr key={cam.id}>
                <td className="font-mono text-xs">{cam.external_camera_id}</td>
                <td>{cam.name}</td>
                <td className="text-xs">{cam.district || '—'}</td>
                <td className="text-xs">{cam.department || '—'}</td>
                <td>{statusBadge(cam.live_status)}</td>
                <td>
                  <button
                    className={`btn btn-sm ${cam.ai_enabled ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => toggleAI(cam)}
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                  >
                    {cam.ai_enabled ? 'AI ON' : 'AI OFF'}
                  </button>
                </td>
                <td className="text-xs font-mono">
                  {cam.latitude ? `${cam.latitude.toFixed(4)}, ${cam.longitude.toFixed(4)}` : '—'}
                </td>
                <td>
                  {cam.hls_url && (
                    <a href={cam.hls_url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">▶</a>
                  )}
                </td>
              </tr>
            ))}
            {cameras.length === 0 && (
              <tr><td colSpan={8} className="text-muted text-sm" style={{ textAlign: 'center', padding: '2rem' }}>No cameras found. Click "Sync from Sandbox" to discover cameras.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
