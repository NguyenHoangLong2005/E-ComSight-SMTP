import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../services/api'
import Header from '../components/Layout/Header'
import { Save, Mail, Bell } from 'lucide-react'

export default function Settings() {
  const { user, updateUser } = useAuth()
  const [form, setForm] = useState({
    full_name: '', shop_name: '',
    alert_email: '', alert_enabled: true, alert_threshold: 'high',
  })
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (user) setForm({
      full_name: user.full_name || '',
      shop_name: user.shop_name || '',
      alert_email: user.alert_email || '',
      alert_enabled: user.alert_enabled !== false,
      alert_threshold: user.alert_threshold || 'high',
    })
  }, [user])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSave = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authAPI.update(form)
      updateUser(form)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      alert('Lỗi cập nhật: ' + (e.response?.data?.detail || e.message))
    } finally { setLoading(false) }
  }

  return (
    <div>
      <Header title="Cài đặt" subtitle="Quản lý tài khoản và cấu hình cảnh báo" />
      <div className="page-content" style={{ maxWidth: 640 }}>
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Profile */}
          <div className="card">
            <div className="card-title mb-4">👤 Thông tin tài khoản</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div className="input-group">
                <label className="input-label">Họ và tên</label>
                <input className="input" value={form.full_name} onChange={e => set('full_name', e.target.value)}
                  placeholder="Nguyễn Văn A" />
              </div>
              <div className="input-group">
                <label className="input-label">Tên cửa hàng</label>
                <input className="input" value={form.shop_name} onChange={e => set('shop_name', e.target.value)}
                  placeholder="My Cosmetics Store" />
              </div>
            </div>
            <div className="input-group mt-3">
              <label className="input-label">Tên đăng nhập (không thể thay đổi)</label>
              <input className="input" value={user?.username || ''} disabled
                style={{ background: 'var(--bg-surface2)', cursor: 'not-allowed' }} />
            </div>
          </div>

          {/* Email Alerts */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <div className="kpi-icon amber"><Bell size={18} /></div>
              <div>
                <div className="card-title">Cấu hình Email Cảnh báo</div>
                <div className="card-subtitle">Nhận email khi có review tiêu cực nghiêm trọng</div>
              </div>
            </div>

            <div className="input-group mb-4">
              <label className="input-label">Email nhận cảnh báo</label>
              <div className="input-icon-wrap">
                <Mail size={15} className="input-icon" />
                <input className="input" type="email" value={form.alert_email}
                  onChange={e => set('alert_email', e.target.value)}
                  placeholder="email@example.com" />
              </div>
            </div>

            <div className="input-group mb-4">
              <label className="input-label">Ngưỡng cảnh báo tối thiểu</label>
              <select className="input" value={form.alert_threshold}
                onChange={e => set('alert_threshold', e.target.value)}>
                <option value="critical">🔴 Nghiêm trọng (hàng giả, kích ứng nguy hiểm)</option>
                <option value="high">🟠 Cao trở lên (+ chất lượng kém, giao muộn)</option>
                <option value="medium">🟡 Trung bình trở lên (tất cả review tiêu cực)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                <div style={{
                  width: 44, height: 24,
                  background: form.alert_enabled ? 'var(--primary-500)' : 'var(--bg-surface2)',
                  borderRadius: 12, position: 'relative', transition: 'var(--transition)',
                  border: '1px solid var(--border)', cursor: 'pointer',
                }} onClick={() => set('alert_enabled', !form.alert_enabled)}>
                  <div style={{
                    width: 18, height: 18, background: 'white',
                    borderRadius: '50%', position: 'absolute',
                    top: 2,
                    left: form.alert_enabled ? 22 : 2,
                    transition: 'var(--transition)',
                    boxShadow: '0 1px 4px rgba(0,0,0,.2)',
                  }} />
                </div>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {form.alert_enabled ? '✅ Bật email cảnh báo' : '❌ Tắt email cảnh báo'}
                </span>
              </label>
            </div>

            {!form.alert_email && (
              <div style={{
                marginTop: 12, padding: '10px 14px', borderRadius: 8,
                background: 'var(--warning-bg)', border: '1px solid #fde68a',
                fontSize: '0.8rem', color: '#92400e',
              }}>
                ⚠️ Cần nhập email để nhận cảnh báo. Dùng Gmail với App Password.
              </div>
            )}
          </div>

          {/* SMTP note */}
          <div style={{
            padding: '14px 18px', borderRadius: 'var(--radius-md)',
            background: 'var(--primary-50)', border: '1px solid var(--primary-200)',
            fontSize: '0.8rem', color: 'var(--primary-800)',
          }}>
            <strong>🔧 Cấu hình SMTP:</strong> Để email hoạt động, cần set environment variables:
            <code style={{ display: 'block', marginTop: 6, padding: '6px 10px',
              background: 'white', borderRadius: 4, fontFamily: 'monospace', fontSize: '0.75rem' }}>
              SMTP_USER=yourmail@gmail.com<br/>
              SMTP_PASSWORD=your_app_password
            </code>
          </div>

          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}
            style={{ width: 'fit-content' }}>
            {loading ? <div className="spinner" style={{ width: 16, height: 16 }} /> : <Save size={17} />}
            {saved ? '✅ Đã lưu!' : 'Lưu thay đổi'}
          </button>
        </form>
      </div>
    </div>
  )
}
