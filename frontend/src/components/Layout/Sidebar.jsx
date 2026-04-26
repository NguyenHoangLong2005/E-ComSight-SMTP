import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, Bell, BarChart2,
  Search, FileDown, Settings, LogOut, ShoppingBag
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useState, useEffect } from 'react'
import { alertsAPI } from '../../services/api'

const navItems = [
  { path: '/',          icon: LayoutDashboard, label: 'Tổng quan' },
  { path: '/reviews',   icon: MessageSquare,   label: 'Đánh giá' },
  { path: '/alerts',    icon: Bell,            label: 'Cảnh báo', badge: true },
  { path: '/analysis',  icon: Search,          label: 'Phân tích live' },
  { path: '/reports',   icon: FileDown,        label: 'Xuất báo cáo' },
  { path: '/settings',  icon: Settings,        label: 'Cài đặt' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    alertsAPI.list({ is_read: false, days: 30 })
      .then(r => setUnread(r.data.unread || 0))
      .catch(() => {})
    const timer = setInterval(() => {
      alertsAPI.list({ is_read: false, days: 30 })
        .then(r => setUnread(r.data.unread || 0))
        .catch(() => {})
    }, 30000)
    return () => clearInterval(timer)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1rem',
          }}>📊</div>
          <div>
            <div className="sidebar-logo-text">E-ComSight</div>
            <div className="sidebar-tagline">Lắng nghe khách hàng, thông minh hơn</div>
          </div>
        </div>
        {user?.shop_name && (
          <div style={{
            marginTop: 12,
            padding: '6px 10px',
            background: 'rgba(59,130,246,.12)',
            borderRadius: 6,
            fontSize: '0.75rem',
            color: '#60a5fa',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}>
            <ShoppingBag size={12} />
            {user.shop_name}
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Menu chính</div>
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={17} className="nav-icon" />
            {item.label}
            {item.badge && unread > 0 && (
              <span className="nav-badge">{unread > 99 ? '99+' : unread}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div style={{
          padding: '10px 8px',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          marginBottom: 8,
        }}>
          <div style={{
            width: 32, height: 32,
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.85rem', fontWeight: 700, color: 'white',
          }}>
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#e2e8f0', truncate: true }}>
              {user?.full_name || user?.username}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Demo account</div>
          </div>
        </div>
        <button className="nav-item" onClick={handleLogout} style={{ color: '#f87171' }}>
          <LogOut size={16} />
          Đăng xuất
        </button>
      </div>
    </aside>
  )
}
