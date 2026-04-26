import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import Sidebar from './components/Layout/Sidebar'
import Login    from './pages/Login'
import Dashboard from './pages/Dashboard'
import Reviews  from './pages/Reviews'
import Alerts   from './pages/Alerts'
import Analysis from './pages/Analysis'
import Reports  from './pages/Reports'
import Settings from './pages/Settings'
import './index.css'

function ProtectedLayout() {
  const { user, loading } = useAuth()

  if (loading) return (
    <div style={{
      height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-base)',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div className="spinner" style={{ width: 36, height: 36, margin: '0 auto 12px',
          borderWidth: 3, borderTopColor: 'var(--primary-500)' }} />
        <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Đang khởi động E-ComSight...</div>
      </div>
    </div>
  )

  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/"          element={<Dashboard />} />
          <Route path="/reviews"   element={<Reviews />} />
          <Route path="/alerts"    element={<Alerts />} />
          <Route path="/analysis"  element={<Analysis />} />
          <Route path="/reports"   element={<Reports />} />
          <Route path="/settings"  element={<Settings />} />
          <Route path="*"          element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/*"     element={<ProtectedLayout />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
