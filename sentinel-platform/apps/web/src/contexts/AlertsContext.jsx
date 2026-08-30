import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { createAlertsWS } from '../api'

const AlertsContext = createContext(null)

export function AlertsProvider({ children }) {
  const [alerts, setAlerts] = useState([])
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((alert) => {
    const id = Date.now()
    setToasts((prev) => [...prev.slice(-4), { ...alert, _toastId: id }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t._toastId !== id)), 8000)
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('sentinel_token')
    if (!token) return
    const ws = createAlertsWS((msg) => {
      if (msg.type === 'ALERT') {
        setAlerts((prev) => [msg, ...prev.slice(0, 99)])
        addToast(msg)
      }
    })
    return () => ws.close()
  }, [addToast])

  return (
    <AlertsContext.Provider value={{ alerts, toasts }}>
      {children}
    </AlertsContext.Provider>
  )
}

export const useAlerts = () => useContext(AlertsContext)
