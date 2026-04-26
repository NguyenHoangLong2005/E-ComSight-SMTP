import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Eye, EyeOff, LogIn, UserPlus } from 'lucide-react'

export default function Login() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', password: '', email: '', full_name: '', shop_name: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPwd, setShowPwd] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        await login(form.username, form.password)
      } else {
        await register(form)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Đã có lỗi xảy ra. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = () => setForm(f => ({ ...f, username: 'demo', password: 'demo1234' }))

  return (
    <div className="login-page">
      <div className="login-card animate-in">
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56,
            background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
            borderRadius: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.5rem', margin: '0 auto 12px',
            boxShadow: '0 8px 24px rgba(59,130,246,.5)',
          }}>📊</div>
          <h1 style={{
            fontSize: '1.8rem', fontWeight: 800,
            background: 'linear-gradient(135deg, #60a5fa, #a78bfa)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            letterSpacing: '-0.5px',
          }}>E-ComSight</h1>
          <p style={{ color: 'rgba(148,163,184,.8)', fontSize: '0.82rem', marginTop: 4 }}>
            Lắng nghe khách hàng, thông minh hơn
          </p>
        </div>

        {/* Tabs */}
        <div className="tabs" style={{ marginBottom: 24 }}>
          <button className={`tab ${mode === 'login' ? 'active' : ''}`} onClick={() => setMode('login')}>
            Đăng nhập
          </button>
          <button className={`tab ${mode === 'register' ? 'active' : ''}`} onClick={() => setMode('register')}>
            Đăng ký
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {mode === 'register' && (
            <>
              <div className="input-group">
                <label className="input-label" style={{ color: 'rgba(148,163,184,.8)' }}>Họ và tên</label>
                <input className="input" value={form.full_name} onChange={e => set('full_name', e.target.value)}
                  placeholder="Nguyễn Văn A" style={{ background: 'rgba(255,255,255,.06)', borderColor: 'rgba(255,255,255,.1)', color: '#f1f5f9' }} />
              </div>
              <div className="input-group">
                <label className="input-label" style={{ color: 'rgba(148,163,184,.8)' }}>Tên cửa hàng</label>
                <input className="input" value={form.shop_name} onChange={e => set('shop_name', e.target.value)}
                  placeholder="My Cosmetics Store" style={{ background: 'rgba(255,255,255,.06)', borderColor: 'rgba(255,255,255,.1)', color: '#f1f5f9' }} />
              </div>
              <div className="input-group">
                <label className="input-label" style={{ color: 'rgba(148,163,184,.8)' }}>Email</label>
                <input className="input" type="email" value={form.email} onChange={e => set('email', e.target.value)}
                  placeholder="email@example.com" required style={{ background: 'rgba(255,255,255,.06)', borderColor: 'rgba(255,255,255,.1)', color: '#f1f5f9' }} />
              </div>
            </>
          )}

          <div className="input-group">
            <label className="input-label" style={{ color: 'rgba(148,163,184,.8)' }}>Tên đăng nhập</label>
            <input className="input" value={form.username} onChange={e => set('username', e.target.value)}
              placeholder="username" required
              style={{ background: 'rgba(255,255,255,.06)', borderColor: 'rgba(255,255,255,.1)', color: '#f1f5f9' }} />
          </div>

          <div className="input-group">
            <label className="input-label" style={{ color: 'rgba(148,163,184,.8)' }}>Mật khẩu</label>
            <div style={{ position: 'relative' }}>
              <input className="input" type={showPwd ? 'text' : 'password'}
                value={form.password} onChange={e => set('password', e.target.value)}
                placeholder="••••••••" required
                style={{ background: 'rgba(255,255,255,.06)', borderColor: 'rgba(255,255,255,.1)', color: '#f1f5f9', paddingRight: 42 }} />
              <button type="button" onClick={() => setShowPwd(!showPwd)} style={{
                position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                color: 'rgba(148,163,184,.6)', background: 'none', border: 'none', cursor: 'pointer',
              }}>
                {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && (
            <div style={{
              padding: '10px 14px', borderRadius: 8,
              background: 'rgba(239,68,68,.15)', border: '1px solid rgba(239,68,68,.3)',
              color: '#f87171', fontSize: '0.82rem',
            }}>
              ⚠️ {error}
            </div>
          )}

          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}
            style={{ marginTop: 4, width: '100%', justifyContent: 'center' }}>
            {loading ? <div className="spinner" style={{ width: 18, height: 18 }} /> :
              mode === 'login' ? <><LogIn size={17} /> Đăng nhập</> : <><UserPlus size={17} /> Tạo tài khoản</>
            }
          </button>
        </form>

        {mode === 'login' && (
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <button onClick={fillDemo} style={{
              background: 'rgba(59,130,246,.1)', border: '1px solid rgba(59,130,246,.3)',
              borderRadius: 8, padding: '8px 16px', color: '#60a5fa', fontSize: '0.8rem',
              cursor: 'pointer', width: '100%', fontFamily: 'var(--font)',
            }}>
              🚀 Dùng tài khoản demo (demo / demo1234)
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
