import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api, { WS_URL } from '../api'
import { format, formatDistanceToNow } from 'date-fns'

/* ── helpers ─────────────────────────────────────────────────── */
const normPlate = (p) => p?.toUpperCase().replace(/[\s\-]/g, '') || ''

const confBadge = (c) => {
  if (c == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>
  const pct = Math.round(c * 100)
  const cls = c >= 0.85 ? 'badge-green' : c >= 0.6 ? 'badge-yellow' : 'badge-red'
  return <span className={`badge ${cls}`}>{pct}%</span>
}

/* ── live YOLO chips ─────────────────────────────────────────── */
function LiveFeed({ onSelect }) {
  const [chips, setChips] = useState([])
  const wsRef = useRef(null)

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/alerts/ws`)
      ws.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data)
          if (d.plate) setChips((prev) => [{ ...d, _ts: Date.now() }, ...prev].slice(0, 14))
        } catch {}
      }
      ws.onclose = () => setTimeout(connect, 3000)
      wsRef.current = ws
    }
    connect()
    return () => wsRef.current?.close()
  }, [])

  return (
    <div style={{
      border: `1px solid ${chips.length ? 'var(--border-accent)' : 'var(--border)'}`,
      borderRadius: 'var(--radius)',
      background: 'var(--bg-glass)',
      overflow: 'hidden',
      marginBottom: '1.25rem',
      transition: 'border-color 0.3s',
    }}>
      <div style={{
        padding: '0.55rem 1rem',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(59,130,246,0.06)',
        display: 'flex', alignItems: 'center', gap: '0.5rem',
      }}>
        <span className="live-dot" />
        <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--accent-cyan)' }}>
          LIVE YOLO DETECTIONS — click to search
        </span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', padding: '0.75rem 1rem', minHeight: 52 }}>
        {chips.length === 0 ? (
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
            Waiting for plate detections from pipeline…
          </span>
        ) : chips.map((d, i) => (
          <button
            key={i}
            onClick={() => onSelect(d.plate)}
            title={`Camera: ${d.camera_id || '?'}`}
            style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.1em',
              padding: '0.28rem 0.7rem', borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-accent)', background: 'rgba(59,130,246,0.13)',
              color: 'var(--accent-cyan)', cursor: 'pointer', transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(59,130,246,0.28)'; e.currentTarget.style.transform = 'scale(1.05)' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(59,130,246,0.13)'; e.currentTarget.style.transform = 'scale(1)' }}
          >
            🚗 {normPlate(d.plate)}
          </button>
        ))}
      </div>
    </div>
  )
}

/* ── snapshot modal ──────────────────────────────────────────── */
function SnapshotModal({ url, onClose }) {
  useEffect(() => {
    const h = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])
  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 999, background: 'rgba(0,0,0,0.85)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(6px)', animation: 'fadeIn 0.15s ease',
    }}>
      <div onClick={e => e.stopPropagation()} style={{ position: 'relative' }}>
        <img src={url} alt="Evidence" style={{ maxWidth: '86vw', maxHeight: '86vh', borderRadius: 'var(--radius)', boxShadow: '0 0 60px rgba(0,0,0,0.8)' }} />
        <button onClick={onClose} style={{
          position: 'absolute', top: -14, right: -14, background: 'var(--accent-red)',
          border: 'none', color: '#fff', borderRadius: '50%', width: 30, height: 30,
          fontSize: '0.9rem', cursor: 'pointer', fontWeight: 700,
        }}>✕</button>
      </div>
    </div>
  )
}

/* ── stat card ───────────────────────────────────────────────── */
function StatCard({ label, value, color, mono }) {
  const cm = { blue: 'var(--accent-blue)', cyan: 'var(--accent-cyan)', green: 'var(--accent-green)' }
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: cm[color] || 'var(--text-primary)', fontFamily: mono ? 'var(--font-mono)' : undefined, fontSize: mono ? '0.82rem' : undefined, letterSpacing: mono ? '0.08em' : undefined }}>
        {value}
      </div>
    </div>
  )
}

/* ── main page ───────────────────────────────────────────────── */
export default function InvestigationPage() {
  const [searchParams] = useSearchParams()
  const [plate, setPlate] = useState(searchParams.get('plate') || '')
  const [results, setResults] = useState([])
  const [timeline, setTimeline] = useState(null)
  const [searching, setSearching] = useState(false)
  const [searched, setSearched] = useState(false)
  const [activeTab, setActiveTab] = useState('table')
  const [previewUrl, setPreviewUrl] = useState(null)
  const navigate = useNavigate()
  const inputRef = useRef(null)

  const doSearch = async (e, overridePlate) => {
    e?.preventDefault()
    const p = normPlate(overridePlate || plate)
    if (!p) return
    setSearching(true); setSearched(false)
    try {
      const [obsRes, tlRes] = await Promise.allSettled([
        api.get('/detections', { params: { plate: p, limit: 200 } }),
        api.get(`/investigation/timeline/${p}`),
      ])
      setResults(obsRes.status === 'fulfilled' ? obsRes.value.data : [])
      setTimeline(tlRes.status === 'fulfilled' ? tlRes.value.data : null)
    } finally { setSearching(false); setSearched(true) }
  }

  useEffect(() => { if (plate) doSearch(null, plate) }, [])

  const handleLiveSelect = (p) => {
    const n = normPlate(p); setPlate(n); doSearch(null, n)
  }

  const cameras = results.length ? new Set(results.map(r => r.camera_id)).size : 0
  const firstSeen = results.length ? results[results.length - 1].observed_at : null
  const lastSeen = results.length ? results[0].observed_at : null
  const avgConf = (() => {
    const cs = results.filter(r => r.plate_confidence != null).map(r => r.plate_confidence)
    return cs.length ? `${Math.round(cs.reduce((a, b) => a + b, 0) / cs.length * 100)}%` : '—'
  })()

  return (
    <div style={{ maxWidth: 1100 }}>
      {/* ── Header ── */}
      <div className="page-header" style={{ marginBottom: '1.25rem' }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.3rem' }}>🔍</span> Vehicle Investigation
          </h1>
          <div className="page-subtitle">Search any plate detected by the YOLO / ANPR pipeline</div>
        </div>
        {searched && results.length > 0 && (
          <button className="btn btn-primary" onClick={() => navigate(`/journey/${normPlate(plate)}`)}>
            🗺 View Journey Map
          </button>
        )}
      </div>

      {/* ── Live YOLO Feed ── */}
      <LiveFeed onSelect={handleLiveSelect} />

      {/* ── Search Bar ── */}
      <form onSubmit={doSearch} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: 380 }}>
          <span style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }}>🔎</span>
          <input
            ref={inputRef}
            id="investigation-plate-input"
            className="input font-mono"
            placeholder="GJ05AB1234"
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
            style={{ width: '100%', fontSize: '1.05rem', letterSpacing: '0.1em', paddingLeft: '2.2rem', border: '1px solid var(--border-accent)', background: 'rgba(59,130,246,0.06)' }}
          />
        </div>
        <button id="investigation-search-btn" type="submit" className="btn btn-primary" disabled={searching} style={{ minWidth: 120 }}>
          {searching ? <><span className="spinner" style={{ width: 15, height: 15 }} /> Searching…</> : '🔍 Search'}
        </button>
        {plate && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setPlate(''); setResults([]); setTimeline(null); setSearched(false) }}>
            ✕ Clear
          </button>
        )}
      </form>

      {/* ── Stats Strip ── */}
      {searched && results.length > 0 && (
        <>
          <div className="stat-grid" style={{ marginBottom: '0.75rem', gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <StatCard label="Plate" value={normPlate(plate)} color="cyan" mono />
            <StatCard label="Total Sightings" value={results.length} color="blue" />
            <StatCard label="Cameras Seen" value={cameras} color="cyan" />
            <StatCard label="Avg Confidence" value={avgConf} color="green" />
          </div>
          <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>FIRST SEEN</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--accent-cyan)' }}>
              {firstSeen ? format(new Date(firstSeen), 'dd MMM yyyy · HH:mm:ss') : '—'}
            </span>
            <span style={{ color: 'var(--border)' }}>→</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>LAST SEEN</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--accent-green)' }}>
              {lastSeen ? format(new Date(lastSeen), 'dd MMM yyyy · HH:mm:ss') : '—'}
            </span>
            <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {lastSeen ? `(${formatDistanceToNow(new Date(lastSeen), { addSuffix: true })})` : ''}
            </span>
          </div>
        </>
      )}

      {/* ── Tabs ── */}
      {searched && results.length > 0 && (
        <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '0.75rem' }}>
          {[{ id: 'table', label: '📋 Detections Table' }, { id: 'timeline', label: '🎞 Camera Timeline' }].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              padding: '0.42rem 1rem', borderRadius: 'var(--radius-sm)', border: '1px solid',
              borderColor: activeTab === t.id ? 'var(--accent-blue)' : 'var(--border)',
              background: activeTab === t.id ? 'rgba(59,130,246,0.18)' : 'var(--bg-glass)',
              color: activeTab === t.id ? 'var(--accent-blue)' : 'var(--text-muted)',
              fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s',
            }}>{t.label}</button>
          ))}
        </div>
      )}

      {/* ── Detections Table ── */}
      {searched && results.length > 0 && activeTab === 'table' && (
        <div className="table-wrap" style={{ animation: 'fadeIn 0.2s ease' }}>
          <table>
            <thead>
              <tr>
                <th>Plate</th>
                <th>Camera ID</th>
                <th>Vehicle Type</th>
                <th>Confidence</th>
                <th>Observed At</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {results.map((obs) => (
                <tr key={obs.id}>
                  <td>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '0.88rem', letterSpacing: '0.08em' }}>
                      {obs.plate_normalised || obs.plate_raw || '—'}
                    </span>
                  </td>
                  <td><span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{obs.camera_id}</span></td>
                  <td><span style={{ fontSize: '0.75rem' }}>{obs.vehicle_type || '—'}</span></td>
                  <td>{confBadge(obs.plate_confidence)}</td>
                  <td style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                    {format(new Date(obs.observed_at), 'dd MMM yyyy HH:mm:ss')}
                  </td>
                  <td>
                    <div className="flex gap-1">
                      {obs.snapshot_path && (
                        <button className="btn btn-ghost btn-sm" title="Full snapshot" onClick={() => setPreviewUrl(obs.snapshot_path)}>📷</button>
                      )}
                      {obs.plate_crop_path && (
                        <button className="btn btn-ghost btn-sm" title="Plate crop" onClick={() => setPreviewUrl(obs.plate_crop_path)}>🔲</button>
                      )}
                      {!obs.snapshot_path && !obs.plate_crop_path && <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>—</span>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Camera Timeline ── */}
      {searched && timeline && activeTab === 'timeline' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', animation: 'fadeIn 0.2s ease' }}>
          {timeline.timeline?.map((entry, i) => (
            <div key={entry.camera_id} style={{
              display: 'flex', gap: '1rem', padding: '1rem 1.25rem',
              background: 'var(--bg-glass)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', position: 'relative', transition: 'border-color 0.2s',
            }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-accent)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{
                minWidth: 36, height: 36, borderRadius: '50%',
                background: 'rgba(59,130,246,0.15)', border: '2px solid var(--accent-blue)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 800, fontSize: '0.78rem', color: 'var(--accent-blue)', flexShrink: 0,
              }}>{i + 1}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{entry.camera_name || entry.camera_id}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>{entry.camera_id}</span>
                  {confBadge(entry.plate_confidence)}
                </div>
                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                  {[{ label: 'First Seen', val: entry.first_seen, color: 'var(--accent-cyan)' }, { label: 'Last Seen', val: entry.last_seen, color: 'var(--accent-green)' }].map(t => (
                    <span key={t.label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <span style={{ fontSize: '0.63rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>{t.label}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: t.color }}>
                        {t.val ? format(new Date(t.val), 'dd MMM · HH:mm:ss') : '—'}
                      </span>
                    </span>
                  ))}
                  {entry.latitude && entry.longitude && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'flex-end' }}>
                      📍 {Number(entry.latitude).toFixed(4)}, {Number(entry.longitude).toFixed(4)}
                    </span>
                  )}
                </div>
              </div>
              {entry.snapshot_path && (
                <img src={entry.snapshot_path} alt="snap" onClick={() => setPreviewUrl(entry.snapshot_path)}
                  style={{ width: 88, height: 58, objectFit: 'cover', borderRadius: 'var(--radius-sm)', cursor: 'pointer', border: '1px solid var(--border)', flexShrink: 0 }}
                  onError={e => { e.currentTarget.style.display = 'none' }}
                />
              )}
              {i < (timeline.timeline?.length - 1) && (
                <div style={{ position: 'absolute', left: 29, bottom: -13, width: 2, height: 13, background: 'var(--border-accent)' }} />
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── No Results ── */}
      {searched && results.length === 0 && !searching && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4rem 2rem', gap: '1rem',
          background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
          animation: 'fadeIn 0.2s ease',
        }}>
          <span style={{ fontSize: '3rem' }}>🔍</span>
          <div style={{ fontWeight: 700, fontSize: '1rem' }}>No observations found</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Plate <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', fontWeight: 700 }}>{normPlate(plate)}</span> has not been detected by any camera yet.
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {!searched && !searching && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4rem 2rem', gap: '1rem',
          background: 'var(--bg-glass)', border: '1px dashed var(--border)', borderRadius: 'var(--radius-lg)',
        }}>
          <span style={{ fontSize: '2.5rem' }}>🚗</span>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
            Enter a plate number above, or click any live YOLO detection chip to instantly search.
          </div>
        </div>
      )}

      {/* ── Snapshot Modal ── */}
      {previewUrl && <SnapshotModal url={previewUrl} onClose={() => setPreviewUrl(null)} />}

      <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }`}</style>
    </div>
  )
}
