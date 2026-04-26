import { useState } from 'react'
import { analysisAPI } from '../services/api'
import Header from '../components/Layout/Header'
import { Send, Link2, FileText, AlertTriangle, CheckCircle, Minus, Zap } from 'lucide-react'

const SENTIMENT_VI = { positive: 'Tích cực', neutral: 'Trung lập', negative: 'Tiêu cực' }
const ASPECT_VI    = { product: 'Chất lượng SP', shipping: 'Vận chuyển', service: 'Dịch vụ', price: 'Giá cả' }
const URGENCY_VI   = { critical: 'Nghiêm trọng', high: 'Cao', medium: 'Trung bình', low: 'Thấp' }

const SENTIMENT_CONFIG = {
  positive: { icon: CheckCircle, color: '#22c55e', bg: 'var(--success-bg)', border: '#bbf7d0' },
  neutral:  { icon: Minus,       color: '#64748b', bg: 'var(--neutral-bg)', border: '#e2e8f0' },
  negative: { icon: AlertTriangle, color: '#ef4444', bg: 'var(--danger-bg)', border: '#fecaca' },
}

function ResultCard({ result }) {
  if (!result) return null
  const cfg = SENTIMENT_CONFIG[result.sentiment_label] || SENTIMENT_CONFIG.neutral
  const Icon = cfg.icon

  return (
    <div className="animate-in" style={{
      border: `1px solid ${cfg.border}`,
      background: cfg.bg,
      borderRadius: 'var(--radius-lg)',
      padding: 24,
      marginTop: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
        <div style={{
          width: 52, height: 52,
          background: 'white',
          borderRadius: 12,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,.1)',
        }}>
          <Icon size={26} color={cfg.color} />
        </div>
        <div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: cfg.color }}>
            {SENTIMENT_VI[result.sentiment_label] || result.sentiment_label}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Độ tin cậy: {result.sentiment_score ? `${(result.sentiment_score * 100).toFixed(1)}%` : '—'}
            {' '}· Nguồn: {result.sentiment_source === 'phobert' ? 'PhoBERT' :
              result.sentiment_source === 'rule' ? 'Rule-based' : 'Ensemble'}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
        <div style={{ background: 'white', borderRadius: 8, padding: '12px 16px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 4 }}>KHÍA CẠNH</div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
            {ASPECT_VI[result.aspect_label] || result.aspect_label || '—'}
          </div>
        </div>
        <div style={{ background: 'white', borderRadius: 8, padding: '12px 16px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 4 }}>MỨC ĐỘ KHẨN</div>
          <div style={{ fontWeight: 700 }}>
            <span className={`badge badge-${result.urgency_label}`}>
              {URGENCY_VI[result.urgency_label] || result.urgency_label || '—'}
            </span>
          </div>
        </div>
        <div style={{ background: 'white', borderRadius: 8, padding: '12px 16px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 4 }}>ĐÃ LƯU</div>
          <div style={{ fontWeight: 700, color: 'var(--success)', fontSize: '0.85rem' }}>
            ✅ Review #{result.review_id}
          </div>
        </div>
      </div>

      {result.explanation && (
        <div style={{
          background: 'white', borderRadius: 8, padding: '12px 16px',
          fontSize: '0.82rem', color: 'var(--text-secondary)',
        }}>
          💡 {result.explanation}
        </div>
      )}
    </div>
  )
}

function URLResultCard({ result }) {
  if (!result || !result.summary) return null
  const { summary, reviews } = result

  return (
    <div className="animate-in card mt-4">
      <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 16 }}>
        🛒 Kết quả phân tích: {result.platform?.toUpperCase()}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 20 }}>
        {[
          { label: 'Tổng reviews', value: summary.total, color: 'var(--primary-600)' },
          { label: '✅ Tích cực', value: `${summary.positive} (${summary.positive_pct}%)`, color: '#22c55e' },
          { label: '⚪ Trung lập', value: summary.neutral, color: '#64748b' },
          { label: '❌ Tiêu cực', value: summary.negative, color: '#ef4444' },
        ].map(item => (
          <div key={item.label} style={{
            padding: '12px', background: 'var(--bg-surface2)', borderRadius: 8, textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: item.color }}>{item.value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.label}</div>
          </div>
        ))}
      </div>

      {/* Top negative reviews */}
      {reviews?.filter(r => r.sentiment_label === 'negative').slice(0, 3).map((r, i) => (
        <div key={i} style={{
          padding: '10px 14px', borderRadius: 8,
          background: 'var(--danger-bg)', border: '1px solid #fecaca',
          marginBottom: 8, fontSize: '0.82rem',
        }}>
          <div style={{ color: '#dc2626', marginBottom: 4 }}>{'★'.repeat(r.rating_star || 1)}</div>
          <div style={{ color: 'var(--text-primary)', fontStyle: 'italic' }}>&ldquo;{r.comment}&rdquo;</div>
        </div>
      ))}
    </div>
  )
}

export default function Analysis() {
  const [mode, setMode]         = useState('text')
  const [text, setText]         = useState('')
  const [url, setUrl]           = useState('')
  const [platform, setPlatform] = useState('manual')
  const [product, setProduct]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [urlResult, setUrlResult] = useState(null)
  const [error, setError]       = useState('')

  const SAMPLE_REVIEWS = [
    'Sản phẩm rất tốt, da mình mịn màng hẳn sau 2 tuần dùng. Shop giao nhanh, đóng gói cẩn thận!',
    'Hàng nhận về bị kích ứng ngay, mặt đỏ và ngứa. Nghi ngờ hàng giả, shop không hỗ trợ đổi trả!',
    'Sản phẩm tạm ổn, không thấy khác biệt nhiều. Giao hàng đúng hẹn, chờ xem thêm.',
    'Giao hàng chậm quá, đặt 7 ngày mới tới. Hộp bị móp nhưng may sản phẩm không vỡ.',
  ]

  const handleTextAnalysis = async () => {
    if (!text.trim()) { setError('Vui lòng nhập nội dung review'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await analysisAPI.analyzeText({ text, platform, product_name: product })
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Phân tích thất bại')
    } finally { setLoading(false) }
  }

  const handleURLAnalysis = async () => {
    if (!url.trim()) { setError('Vui lòng nhập URL sản phẩm'); return }
    setLoading(true); setError(''); setUrlResult(null)
    try {
      const res = await analysisAPI.analyzeURL({ url })
      setUrlResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Không thể lấy reviews từ URL này')
    } finally { setLoading(false) }
  }

  return (
    <div>
      <Header title="Phân tích Live" subtitle="Phân tích cảm xúc review theo thời gian thực" />
      <div className="page-content">

        {/* Mode tabs */}
        <div className="tabs mb-4" style={{ width: 'fit-content' }}>
          <button className={`tab ${mode === 'text' ? 'active' : ''}`} onClick={() => { setMode('text'); setResult(null); setUrlResult(null) }}>
            <FileText size={14} style={{ marginRight: 6 }} />
            Nhập text
          </button>
          <button className={`tab ${mode === 'url' ? 'active' : ''}`} onClick={() => { setMode('url'); setResult(null); setUrlResult(null) }}>
            <Link2 size={14} style={{ marginRight: 6 }} />
            Phân tích URL
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
          {/* Input Panel */}
          <div className="card">
            {mode === 'text' ? (
              <>
                <div className="card-header">
                  <div>
                    <div className="card-title">📝 Nhập review để phân tích</div>
                    <div className="card-subtitle">Hỗ trợ tiếng Việt với PhoBERT AI</div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                  <select className="input" style={{ flex: 1 }}
                    value={platform} onChange={e => setPlatform(e.target.value)}>
                    <option value="manual">✏️ Nhập thủ công</option>
                    <option value="shopee">🛍️ Shopee</option>
                    <option value="tiktok">🎵 TikTok</option>
                  </select>
                  <input className="input" style={{ flex: 1 }}
                    placeholder="Tên sản phẩm (tùy chọn)"
                    value={product} onChange={e => setProduct(e.target.value)} />
                </div>

                <textarea className="input" rows={6}
                  placeholder="Nhập nội dung review tiếng Việt để phân tích cảm xúc..."
                  value={text} onChange={e => setText(e.target.value)}
                  style={{ resize: 'vertical', marginBottom: 12 }} />

                {/* Sample reviews */}
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                    💡 Thử với mẫu:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {SAMPLE_REVIEWS.map((s, i) => (
                      <button key={i} className="btn btn-ghost btn-sm"
                        style={{ textAlign: 'left', justifyContent: 'flex-start', fontSize: '0.75rem' }}
                        onClick={() => setText(s)}>
                        {s.slice(0, 70)}...
                      </button>
                    ))}
                  </div>
                </div>

                {error && <div style={{ color: 'var(--danger)', fontSize: '0.82rem', marginBottom: 10 }}>⚠️ {error}</div>}

                <button className="btn btn-primary w-full" onClick={handleTextAnalysis} disabled={loading}>
                  {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Đang phân tích...</>
                    : <><Zap size={16} /> Phân tích ngay</>}
                </button>
              </>
            ) : (
              <>
                <div className="card-header">
                  <div>
                    <div className="card-title">🔗 Phân tích URL sản phẩm</div>
                    <div className="card-subtitle">Tự động lấy và phân tích reviews từ Shopee / TikTok</div>
                  </div>
                </div>

                <div className="input-group mb-4">
                  <label className="input-label">URL sản phẩm</label>
                  <input className="input" placeholder="https://shopee.vn/product/..."
                    value={url} onChange={e => setUrl(e.target.value)} />
                </div>

                <div style={{
                  padding: '12px 16px', borderRadius: 8,
                  background: 'var(--bg-surface2)', marginBottom: 16,
                  fontSize: '0.8rem', color: 'var(--text-muted)',
                }}>
                  ℹ️ Hỗ trợ URL sản phẩm từ shopee.vn. Sẽ tự động lấy và phân tích tối đa 50 reviews mới nhất.
                </div>

                {error && <div style={{ color: 'var(--danger)', fontSize: '0.82rem', marginBottom: 10 }}>⚠️ {error}</div>}

                <button className="btn btn-primary w-full" onClick={handleURLAnalysis} disabled={loading}>
                  {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Đang lấy reviews...</>
                    : <><Link2 size={16} /> Phân tích URL</>}
                </button>
              </>
            )}
          </div>

          {/* Result Panel */}
          <div>
            {!result && !urlResult && !loading && (
              <div className="card empty-state" style={{ minHeight: 300, justifyContent: 'center', display: 'flex', alignItems: 'center', flexDirection: 'column' }}>
                <div style={{ fontSize: 48, marginBottom: 12 }}>🤖</div>
                <div className="empty-state-title">Kết quả phân tích sẽ hiển thị ở đây</div>
                <div className="empty-state-desc">Nhập review hoặc URL sản phẩm và nhấn phân tích</div>
              </div>
            )}
            {mode === 'text' && result && <ResultCard result={result} />}
            {mode === 'url' && urlResult && <URLResultCard result={urlResult} />}
          </div>
        </div>
      </div>
    </div>
  )
}
