import React from 'react'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { AlertsProvider, useAlerts } from './contexts/AlertsContext'

// Pages
import LoginPage from './pages/LoginPage'
import CommandCentre from './pages/CommandCentre'
import CameraRegistry from './pages/CameraRegistry'
import GISMap from './pages/GISMap'
import LiveControlRoom from './pages/LiveControlRoom'
import WatchlistPage from './pages/WatchlistPage'
import AlertsPage from './pages/AlertsPage'
import InvestigationPage from './pages/InvestigationPage'
import VehicleJourneyPage from './pages/VehicleJourneyPage'
import CameraHealthPage from './pages/CameraHealthPage'
import AuditLogsPage from './pages/AuditLogsPage'

const NAV = [
  { section: 'Overview', items: [
    { label: '⬛ Command Centre', to: '/', id: 'nav-command' },
  ]},
  { section: 'Operations', items: [
    { label: '📷 Camera Registry', to: '/cameras', id: 'nav-cameras' },
    { label: '🗺 GIS Map', to: '/gis', id: 'nav-gis' },
    { label: '📺 Live Control Room', to: '/live', id: 'nav-live' },
  ]},
  { section: 'Intelligence', items: [
    { label: '🚨 Alerts', to: '/alerts', id: 'nav-alerts' },
    { label: '📋 Watchlist', to: '/watchlist', id: 'nav-watchlist' },
    { label: '🔍 Investigation', to: '/investigation', id: 'nav-investigation' },
  ]},
  { section: 'System', items: [
    { label: '💚 Camera Health', to: '/health', id: 'nav-health' },
    { label: '📜 Audit Logs', to: '/audit', id: 'nav-audit' },
  ]},
]

function AlertBadge() {
  const { alerts } = useAlerts()
  const open = alerts.filter((a) => a.severity === 'CRITICAL' || a.match_type === 'EXACT').length
  if (!open) return null
  return (
    <span style={{
      background: 'var(--accent-red)',
      color: '#fff',
      borderRadius: '999px',
      fontSize: '0.6rem',
      fontWeight: 700,
      padding: '1px 6px',
      marginLeft: 'auto',
    }}>{open}</span>
  )
}

function ToastContainer() {
  const { toasts } = useAlerts()
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t._toastId} className="toast toast-alert">
          <div style={{ color: 'var(--accent-red)', fontSize: '1.2rem' }}>🚨</div>
          <div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
              Watchlist Match — {t.match_type}
            </div>
            <div style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '1rem', color: 'var(--accent-red)', marginTop: 2 }}>
              {t.plate}
            </div>
            <div className="text-xs text-muted">{t.camera_id}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="layout">
      {/* Topbar */}
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">◈</span>
          <span>SENTINEL</span>
          <span className="brand-dot">·</span>
          <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.9rem' }}>Gujarat Police Intelligence Platform</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="live-dot" />
          <span className="text-xs text-muted">LIVE</span>
          {user && (
            <>
              <span className="text-xs text-muted" style={{ marginLeft: '0.5rem' }}>{user.full_name}</span>
              <span className={`badge badge-blue`}>{user.role}</span>
              <button className="btn btn-ghost btn-sm" onClick={logout}>Sign Out</button>
            </>
          )}
        </div>
      </header>

      {/* Sidebar */}
      <nav className="sidebar">
        {NAV.map((section) => (
          <div key={section.section} className="nav-section">
            <div className="nav-label">{section.section}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                id={item.id}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                {item.label}
                {item.to === '/alerts' && <AlertBadge />}
              </NavLink>
            ))}
          </div>
        ))}

        {/* User info */}
        <div style={{ marginTop: 'auto', padding: '1rem 1.25rem', borderTop: '1px solid var(--border)' }}>
          <div className="text-xs text-muted">Gujarat Police</div>
          <div className="text-xs text-muted">Sentinel v1.0</div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<CommandCentre />} />
          <Route path="/cameras" element={<CameraRegistry />} />
          <Route path="/gis" element={<GISMap />} />
          <Route path="/live" element={<LiveControlRoom />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/investigation" element={<InvestigationPage />} />
          <Route path="/journey/:plate" element={<VehicleJourneyPage />} />
          <Route path="/health" element={<CameraHealthPage />} />
          <Route path="/audit" element={<AuditLogsPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>

      <ToastContainer />
    </div>
  )
}

function ProtectedApp() {
  const { user, loading } = useAuth()
  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <span className="spinner" style={{ width: 40, height: 40 }} />
    </div>
  )
  if (!user) return <LoginPage />
  return <AppLayout />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AlertsProvider>
          <ProtectedApp />
        </AlertsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
