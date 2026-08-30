import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../api'

export default function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)',
      backgroundImage: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(59,130,246,0.12) 0%, transparent 60%)',
    }}>
      <div style={{ width: 380 }}>
        {/* Brand */}
        <div className="brand" style={{ justifyContent: 'center', marginBottom: '2rem', fontSize: '1.4rem' }}>
          <span className="brand-icon">◈</span>
          <span>SENTINEL</span>
          <span className="brand-dot">·</span>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>Intelligence Platform</span>
        </div>

        <div className="card" style={{ padding: '2rem' }}>
          <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
            <div className="page-title" style={{ fontSize: '1.1rem' }}>Control Room Access</div>
            <div className="page-subtitle">Gujarat Police — Authorised Personnel Only</div>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                id="login-email"
                type="email"
                className="input"
                placeholder="officer@police.gujarat.gov.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                id="login-password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            {error && (
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius)', padding: '0.6rem 0.75rem', color: 'var(--accent-red)', fontSize: '0.82rem' }}>
                {error}
              </div>
            )}
            <button id="login-submit" type="submit" className="btn btn-primary w-full" disabled={loading} style={{ justifyContent: 'center', padding: '0.65rem' }}>
              {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Sign In'}
            </button>
          </form>
        </div>

        <div style={{ textAlign: 'center', marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.72rem' }}>
          Gujarat Police Innovation Hackathon 2026 · Sentinel Platform
        </div>
      </div>
    </div>
  )
}
