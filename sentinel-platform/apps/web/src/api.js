import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sentinel_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('sentinel_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// WebSocket helper
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
export function createAlertsWS(onMessage) {
  const ws = new WebSocket(`${WS_URL}/alerts/ws`)
  ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)) } catch {} }
  ws.onclose = () => { setTimeout(() => createAlertsWS(onMessage), 3000) }
  return ws
}
