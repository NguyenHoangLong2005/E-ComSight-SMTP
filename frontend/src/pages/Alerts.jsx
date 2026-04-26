import { useState, useEffect } from 'react'
import { alertsAPI } from '../services/api'
import Header from '../components/Layout/Header'
import { Bell, CheckCheck, Trash2, AlertTriangle, RefreshCw } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { vi } from 'date-fns/locale'

const URGENCY_CONFIG = {
  critical: { color: '#ef4444', label: 'Nghiêm trọng', icon: '🔴' },
  high:     { color: '#f97316', label: 'Cao',          icon: '🟠' },
  medium:   { color: '#f59e0b', label: 'Trung bình',   icon: '🟡' },
  low:      { color: '#22c55e', label: 'Thấp',         icon: '🟢' },
}

export default function Alerts() {
  const [alerts, setAlerts]   = useState([])
  const [unread, setUnread]   = useState(0)
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter]   = useState({ urgency: '', is_read: '' })

  const load = async () => {
    setLoading(true)
    try {
      const params = { days: 90, page: 1, page_size: 50 }
      if (filter.urgency) params.urgency = filter.urgency
      if (filter.is_read !== '') params.is_read = filter.is_read === 'true'
      const res = await alertsAPI.list(params)
      setAlerts(res.data.items || [])
      setUnread(res.data.unread || 0)
      setTotal(res.data.total || 0)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filter])

  const markRead = async (id) => {
    await alertsAPI.markRead(id)
    setAlerts(as => as.map(a => a.id === id ? { ...a, is_read: true } : a))
    setUnread(u => Math.max(0, u - 1))
  }

  const markAll = async () => {
    await alertsAPI.markAllRead()
    setAlerts(as => as.map(a => ({ ...a, is_read: true })))
    setUnread(0)
  }

  const remove = async (id) => {
    await alertsAPI.remove(id)
    setAlerts(as => as.filter(a => a.id !== id))
    setTotal(t => t - 1)
  }

  const formatTime = (dateStr) => {
    try {
      return formatDistanceToNow(new Date(dateStr + 'Z'), { addSuffix: true, locale: vi })
    } catch { return dateStr }
  }

  return (
    <div>
      <Header title="Hệ thống Cảnh báo" subtitle={`${unread} cảnh báo chưa đọc`} />
      <div className="page-content">

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
          {Object.entries(URGENCY_CONFIG).map(([key, cfg]) => {
            const count = alerts.filter(a => a.urgency === key).length
            return (
              <div key={key} className="card" style={{ padding: 16, borderLeft: `3px solid ${cfg.color}` }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: cfg.color }}>{count}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{cfg.icon} {cfg.label}</div>
              </div>
            )
          })}
        </div>

        {/* Toolbar */}
        <div className="card mb-4">
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
            <select className="input" style={{ width: 150 }}
              value={filter.urgency} onChange={e => setFilter(f => ({ ...f, urgency: e.target.value }))}>
              <option value="">Tất cả mức độ</option>
              <option value="critical">🔴 Nghiêm trọng</option>
              <option value="high">🟠 Cao</option>
              <option value="medium">🟡 Trung bình</option>
              <option value="low">🟢 Thấp</option>
            </select>

            <select className="input" style={{ width: 140 }}
              value={filter.is_read} onChange={e => setFilter(f => ({ ...f, is_read: e.target.value }))}>
              <option value="">Tất cả trạng thái</option>
              <option value="false">Chưa đọc</option>
              <option value="true">Đã đọc</option>
            </select>

            <button className="btn btn-secondary" onClick={load}><RefreshCw size={15} /> Làm mới</button>

            {unread > 0 && (
              <button className="btn btn-primary" onClick={markAll}>
                <CheckCheck size={15} /> Đánh dấu tất cả đã đọc
              </button>
            )}
          </div>
        </div>

        {/* Alert List */}
        <div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 48 }}>
              <div className="spinner" style={{ margin: '0 auto' }} />
            </div>
          ) : alerts.length === 0 ? (
            <div className="card empty-state">
              <div className="empty-state-icon">🎉</div>
              <div className="empty-state-title">Không có cảnh báo nào</div>
              <div className="empty-state-desc">Tất cả đều ổn! Không có review nghiêm trọng.</div>
            </div>
          ) : (
            alerts.map(alert => {
              const cfg = URGENCY_CONFIG[alert.urgency] || URGENCY_CONFIG.low
              return (
                <div key={alert.id} className={`alert-item ${alert.urgency} ${alert.is_read ? '' : 'unread'} animate-in`}>
                  <div className={`alert-dot ${alert.urgency}`} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                      <div>
                        <div className="alert-title">
                          {!alert.is_read && (
                            <span style={{
                              display: 'inline-block', width: 7, height: 7,
                              background: 'var(--danger)', borderRadius: '50%',
                              marginRight: 7,
                            }} />
                          )}
                          {alert.title}
                        </div>
                        <div className="alert-message">{alert.message}</div>
                        <div className="alert-meta">
                          <span className={`badge badge-${alert.urgency}`} style={{ marginRight: 8 }}>
                            {cfg.icon} {cfg.label}
                          </span>
                          {alert.product_name && <span>📦 {alert.product_name} · </span>}
                          {alert.platform && <span>🛒 {alert.platform} · </span>}
                          🕐 {formatTime(alert.created_at)}
                          {alert.is_email_sent && <span style={{ color: 'var(--success)', marginLeft: 8 }}>✉️ Email đã gửi</span>}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                        {!alert.is_read && (
                          <button className="btn btn-secondary btn-sm" onClick={() => markRead(alert.id)}>
                            <CheckCheck size={13} /> Đã đọc
                          </button>
                        )}
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={() => remove(alert.id)}
                          style={{ color: 'var(--danger)' }}>
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
