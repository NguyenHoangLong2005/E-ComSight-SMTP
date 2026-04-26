import { useState, useEffect } from 'react'
import { analyticsAPI } from '../services/api'
import Header from '../components/Layout/Header'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
  BarChart, Bar,
} from 'recharts'
import { TrendingUp, TrendingDown, MessageSquare, AlertTriangle, ThumbsUp, Minus } from 'lucide-react'

const SENTIMENT_COLORS = {
  positive: '#22c55e',
  neutral:  '#64748b',
  negative: '#ef4444',
}

const ASPECT_LABELS = {
  product:  'Chất lượng SP',
  shipping: 'Vận chuyển',
  service:  'Dịch vụ bán',
  price:    'Giá cả',
}

const DAYS_OPTIONS = [
  { label: '7 ngày', value: 7 },
  { label: '30 ngày', value: 30 },
  { label: '90 ngày', value: 90 },
]

function KPICard({ icon: Icon, label, value, subValue, color, change }) {
  return (
    <div className={`kpi-card ${color}`}>
      <div className="flex items-center justify-between">
        <div className={`kpi-icon ${color}`}><Icon size={20} /></div>
        {change !== undefined && (
          <span className={`kpi-change ${change >= 0 ? 'up' : 'down'}`}>
            {change >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
            {Math.abs(change)}%
          </span>
        )}
      </div>
      <div>
        <div className="kpi-value">{value}</div>
        <div className="kpi-label">{label}</div>
        {subValue && <div className="text-xs text-muted mt-1">{subValue}</div>}
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '10px 14px', boxShadow: 'var(--shadow-lg)',
      fontSize: '0.82rem',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: 'flex', gap: 8, alignItems: 'center' }}>
          <span>●</span> {p.name}: <b>{p.value}</b>
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [days, setDays]         = useState(30)
  const [overview, setOverview] = useState(null)
  const [trend, setTrend]       = useState([])
  const [aspects, setAspects]   = useState([])
  const [products, setProducts] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      analyticsAPI.overview({ days }),
      analyticsAPI.trend({ days }),
      analyticsAPI.aspects({ days }),
      analyticsAPI.topProducts({ days, sort_by: 'negative', limit: 5 }),
    ])
      .then(([ov, tr, asp, prod]) => {
        setOverview(ov.data)
        setTrend(tr.data.data || [])
        setAspects(asp.data.data || [])
        setProducts(prod.data.data || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [days])

  const sentimentPieData = overview ? [
    { name: 'Tích cực', value: overview.sentiment_distribution.positive, color: '#22c55e' },
    { name: 'Trung lập', value: overview.sentiment_distribution.neutral,  color: '#64748b' },
    { name: 'Tiêu cực', value: overview.sentiment_distribution.negative, color: '#ef4444' },
  ] : []

  const aspectData = aspects.map(a => ({
    ...a,
    name: ASPECT_LABELS[a.aspect] || a.aspect,
  }))

  return (
    <div>
      <Header title="Tổng quan" subtitle="Phân tích cảm xúc khách hàng theo thời gian thực" />
      <div className="page-content">
        {/* Period selector */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
          <div className="tabs" style={{ width: 'fit-content' }}>
            {DAYS_OPTIONS.map(o => (
              <button key={o.value} className={`tab ${days === o.value ? 'active' : ''}`}
                onClick={() => setDays(o.value)}>
                {o.label}
              </button>
            ))}
          </div>
        </div>

        {/* KPI Cards */}
        <div className="kpi-grid mb-6">
          <KPICard icon={MessageSquare} label="Tổng reviews" color="blue"
            value={loading ? '—' : overview?.total_reviews?.toLocaleString() || 0}
            subValue={`${days} ngày qua`} />
          <KPICard icon={ThumbsUp} label="Tỷ lệ tích cực" color="green"
            value={loading ? '—' : `${overview?.positive_rate || 0}%`}
            subValue="Positive rate" />
          <KPICard icon={Minus} label="Review tiêu cực" color="red"
            value={loading ? '—' : overview?.negative_count || 0}
            subValue="Cần chú ý" />
          <KPICard icon={AlertTriangle} label="Cảnh báo khẩn" color="amber"
            value={loading ? '—' : overview?.alerts_count || 0}
            subValue="Critical + High" />
        </div>

        {/* Charts Row 1 */}
        <div className="chart-grid mb-4">
          {/* Sentiment Donut */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Phân phối Cảm xúc</div>
                <div className="card-subtitle">Tỷ lệ Positive / Neutral / Negative</div>
              </div>
            </div>
            {loading ? (
              <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner" />
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <ResponsiveContainer width="60%" height={240}>
                  <PieChart>
                    <Pie data={sentimentPieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                      paddingAngle={3} dataKey="value">
                      {sentimentPieData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => [v, 'Reviews']} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ flex: 1 }}>
                  {sentimentPieData.map(item => (
                    <div key={item.name} style={{ marginBottom: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 4 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                          <span style={{ width: 8, height: 8, borderRadius: '50%', background: item.color, display: 'inline-block' }} />
                          {item.name}
                        </span>
                        <span style={{ fontWeight: 700 }}>
                          {overview?.total_reviews ? Math.round(item.value / overview.total_reviews * 100) : 0}%
                        </span>
                      </div>
                      <div className="progress">
                        <div className="progress-bar" style={{
                          width: `${overview?.total_reviews ? item.value / overview.total_reviews * 100 : 0}%`,
                          background: item.color,
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Trend Chart */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Xu hướng theo thời gian</div>
                <div className="card-subtitle">Số lượng reviews theo ngày</div>
              </div>
            </div>
            {loading ? (
              <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                    tickFormatter={v => v?.slice(5)} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line type="monotone" dataKey="positive" stroke="#22c55e" strokeWidth={2} dot={false} name="Tích cực" />
                  <Line type="monotone" dataKey="neutral"  stroke="#64748b" strokeWidth={2} dot={false} name="Trung lập" />
                  <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} dot={false} name="Tiêu cực" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="chart-grid">
          {/* Aspect Analysis */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Phân tích theo Khía cạnh</div>
                <div className="card-subtitle">Cảm xúc theo từng dịch vụ</div>
              </div>
            </div>
            {loading ? (
              <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={aspectData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                  <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="positive" fill="#22c55e" name="Tích cực" stackId="a" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="neutral"  fill="#64748b" name="Trung lập" stackId="a" />
                  <Bar dataKey="negative" fill="#ef4444" name="Tiêu cực" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Top Products */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Sản phẩm cần chú ý</div>
                <div className="card-subtitle">Top sản phẩm có nhiều review tiêu cực</div>
              </div>
            </div>
            {loading ? (
              <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner" />
              </div>
            ) : products.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🎉</div>
                <div className="empty-state-title">Không có sản phẩm cần chú ý</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {products.map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 28, height: 28,
                      background: i === 0 ? 'var(--danger-bg)' : 'var(--bg-surface2)',
                      color: i === 0 ? 'var(--danger)' : 'var(--text-muted)',
                      borderRadius: 6,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.75rem', fontWeight: 700, flexShrink: 0,
                    }}>
                      {i + 1}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {p.name}
                      </div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                        <div className="progress" style={{ flex: 1, height: 5 }}>
                          <div className="progress-bar"
                            style={{ width: `${p.total ? p.negative / p.total * 100 : 0}%`, background: '#ef4444' }} />
                        </div>
                        <span style={{ fontSize: '0.72rem', color: 'var(--danger)', whiteSpace: 'nowrap' }}>
                          {p.negative} tiêu cực
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
