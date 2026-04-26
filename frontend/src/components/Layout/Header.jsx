import { Sun, Moon, Bell } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export default function Header({ title, subtitle }) {
  const { isDark, toggle } = useTheme()

  return (
    <header className="header">
      <div>
        <div className="header-title">{title}</div>
        {subtitle && <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 1 }}>{subtitle}</div>}
      </div>
      <div className="header-actions">
        {/* Dark mode toggle */}
        <button
          className="btn btn-ghost btn-icon"
          onClick={toggle}
          title={isDark ? 'Chế độ sáng' : 'Chế độ tối'}
          style={{ color: isDark ? '#fbbf24' : 'var(--text-muted)' }}
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  )
}
