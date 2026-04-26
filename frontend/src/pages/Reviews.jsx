import { useState, useEffect, useRef } from 'react'
import { reviewsAPI } from '../services/api'
import Header from '../components/Layout/Header'
import { Search, Filter, Upload, RefreshCw, ChevronLeft, ChevronRight, Edit2, Star } from 'lucide-react'

const SENTIMENT_LABELS = { positive: 'Tích cực', neutral: 'Trung lập', negative: 'Tiêu cực' }
const ASPECT_LABELS    = { product: 'Chất lượng SP', shipping: 'Vận chuyển', service: 'Dịch vụ', price: 'Giá cả' }
const URGENCY_LABELS   = { critical: 'Nghiêm trọng', high: 'Cao', medium: 'Trung bình', low: 'Thấp' }

function Stars({ count }) {
  return <span className="stars">{'★'.repeat(count)}{'☆'.repeat(5 - count)}</span>
}

function SentimentBadge({ label }) {
  return <span className={`badge badge-${label || 'neutral'}`}>{SENTIMENT_LABELS[label] || label || '—'}</span>
}

function UrgencyBadge({ label }) {
  if (!label) return null
  return <span className={`badge badge-${label}`}>{URGENCY_LABELS[label] || label}</span>
}

function PlatformBadge({ platform }) {
  const icons = { shopee: '🛍️', tiktok: '🎵', manual: '✏️', import: '📥' }
  return <span className={`badge badge-${platform || 'manual'}`}>{icons[platform] || '📦'} {platform || 'N/A'}</span>
}

export default function Reviews() {
  const fileRef = useRef()
  const [reviews, setReviews]   = useState([])
  const [total, setTotal]       = useState(0)
  const [page, setPage]         = useState(1)
  const [loading, setLoading]   = useState(false)
  const [importing, setImporting] = useState(false)
  const [filters, setFilters]   = useState({
    search: '', platform: '', sentiment: '', aspect: '', urgency: '', page_size: 20
  })
  const [editRow, setEditRow]   = useState(null)

  const PAGE_SIZE = 20

  const load = async (pg = page) => {
    setLoading(true)
    try {
      const params = { page: pg, page_size: PAGE_SIZE, ...filters }
      Object.keys(params).forEach(k => !params[k] && delete params[k])
      const res = await reviewsAPI.list(params)
      setReviews(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load(1); setPage(1) }, [filters])
  useEffect(() => { load(page) }, [page])

  const handleImport = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    try {
      const res = await reviewsAPI.importCSV(file)
      alert(`✅ ${res.data.message}`)
      load(1)
    } catch (err) {
      alert(`❌ Lỗi: ${err.response?.data?.detail || err.message}`)
    } finally { setImporting(false); e.target.value = '' }
  }

  const handleUpdateLabel = async (reviewId, field, value) => {
    try {
      await reviewsAPI.update(reviewId, { [field]: value, is_labeled: true })
      setReviews(rs => rs.map(r => r.id === reviewId ? { ...r, [field]: value, is_labeled: true } : r))
    } catch (e) { console.error(e) }
  }

  const setFilter = (k, v) => setFilters(f => ({ ...f, [k]: v }))
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div>
      <Header title="Quản lý Đánh giá" subtitle={`Tổng: ${total.toLocaleString()} reviews`} />
      <div className="page-content">

        {/* Toolbar */}
        <div className="card mb-4">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {/* Search */}
            <div className="input-icon-wrap" style={{ flex: 1, minWidth: 220 }}>
              <Search size={15} className="input-icon" />
              <input className="input" placeholder="Tìm kiếm nội dung review..."
                value={filters.search} onChange={e => setFilter('search', e.target.value)} />
            </div>

            {/* Platform */}
            <select className="input" style={{ width: 140 }}
              value={filters.platform} onChange={e => setFilter('platform', e.target.value)}>
              <option value="">Tất cả nền tảng</option>
              <option value="shopee">🛍️ Shopee</option>
              <option value="tiktok">🎵 TikTok</option>
              <option value="manual">✏️ Thủ công</option>
            </select>

            {/* Sentiment */}
            <select className="input" style={{ width: 140 }}
              value={filters.sentiment} onChange={e => setFilter('sentiment', e.target.value)}>
              <option value="">Tất cả cảm xúc</option>
              <option value="positive">✅ Tích cực</option>
              <option value="neutral">⚪ Trung lập</option>
              <option value="negative">❌ Tiêu cực</option>
            </select>

            {/* Urgency */}
            <select className="input" style={{ width: 150 }}
              value={filters.urgency} onChange={e => setFilter('urgency', e.target.value)}>
              <option value="">Tất cả mức độ</option>
              <option value="critical">🔴 Nghiêm trọng</option>
              <option value="high">🟠 Cao</option>
              <option value="medium">🟡 Trung bình</option>
              <option value="low">🟢 Thấp</option>
            </select>

            <button className="btn btn-secondary" onClick={() => load(page)}>
              <RefreshCw size={15} /> Làm mới
            </button>

            {/* Import CSV */}
            <button className="btn btn-primary" onClick={() => fileRef.current?.click()} disabled={importing}>
              {importing ? <div className="spinner" style={{ width: 15, height: 15 }} /> : <Upload size={15} />}
              Import CSV
            </button>
            <input ref={fileRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={handleImport} />
          </div>
        </div>

        {/* Table */}
        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Nền tảng</th>
                  <th>Sản phẩm</th>
                  <th>Nội dung review</th>
                  <th>Sao</th>
                  <th>Cảm xúc</th>
                  <th>Độ tin cậy</th>
                  <th>Khía cạnh</th>
                  <th>Mức khẩn</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={10} style={{ textAlign: 'center', padding: 40 }}>
                    <div className="spinner" style={{ margin: '0 auto' }} />
                  </td></tr>
                ) : reviews.length === 0 ? (
                  <tr><td colSpan={10}>
                    <div className="empty-state">
                      <div className="empty-state-icon">📋</div>
                      <div className="empty-state-title">Không có reviews</div>
                      <div className="empty-state-desc">Import CSV hoặc thêm review mới để bắt đầu</div>
                    </div>
                  </td></tr>
                ) : reviews.map((r, i) => (
                  <tr key={r.id}>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                      {(page - 1) * PAGE_SIZE + i + 1}
                    </td>
                    <td><PlatformBadge platform={r.platform} /></td>
                    <td style={{ fontSize: '0.8rem', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.product_name || '—'}
                    </td>
                    <td>
                      <div className="table-comment">{r.comment}</div>
                    </td>
                    <td><Stars count={r.rating_star || 0} /></td>
                    <td>
                      {editRow === r.id ? (
                        <select className="input" style={{ fontSize: '0.78rem', padding: '4px 8px' }}
                          value={r.sentiment_label || ''}
                          onChange={e => { handleUpdateLabel(r.id, 'sentiment_label', e.target.value); setEditRow(null) }}>
                          <option value="positive">✅ Tích cực</option>
                          <option value="neutral">⚪ Trung lập</option>
                          <option value="negative">❌ Tiêu cực</option>
                        </select>
                      ) : <SentimentBadge label={r.sentiment_label} />}
                    </td>
                    <td style={{ fontSize: '0.78rem' }}>
                      {r.sentiment_score ? `${(r.sentiment_score * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {ASPECT_LABELS[r.aspect_label] || r.aspect_label || '—'}
                      </span>
                    </td>
                    <td><UrgencyBadge label={r.urgency_label} /></td>
                    <td>
                      <button className="btn btn-ghost btn-sm btn-icon"
                        onClick={() => setEditRow(editRow === r.id ? null : r.id)}
                        title="Gán nhãn thủ công">
                        <Edit2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button className="btn btn-secondary btn-sm btn-icon"
                disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
                <ChevronLeft size={15} />
              </button>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                Trang {page} / {totalPages}
              </span>
              <button className="btn btn-secondary btn-sm btn-icon"
                disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
                <ChevronRight size={15} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
