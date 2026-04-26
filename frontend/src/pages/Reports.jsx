import { useState } from 'react'
import { exportAPI, downloadBlob } from '../services/api'
import Header from '../components/Layout/Header'
import { FileText, FileSpreadsheet, FileDown, Download } from 'lucide-react'

const EXPORT_OPTIONS = [
  {
    id: 'csv',
    icon: FileText,
    title: 'Xuất CSV',
    desc: 'File .csv dùng để gán nhãn thủ công, nhập vào Google Sheets hoặc Excel.',
    color: 'green',
    ext: '.csv',
  },
  {
    id: 'excel',
    icon: FileSpreadsheet,
    title: 'Xuất Excel',
    desc: 'File .xlsx với định dạng màu sắc theo cảm xúc, kèm sheet tổng quan.',
    color: 'blue',
    ext: '.xlsx',
  },
  {
    id: 'pdf',
    icon: FileDown,
    title: 'Xuất PDF Báo cáo',
    desc: 'Báo cáo PDF chuyên nghiệp với tổng quan và danh sách cảnh báo quan trọng.',
    color: 'amber',
    ext: '.pdf',
  },
]

export default function Reports() {
  const [days, setDays]         = useState(30)
  const [platform, setPlatform] = useState('')
  const [loadingId, setLoadingId] = useState(null)

  const handleExport = async (type) => {
    setLoadingId(type)
    try {
      const params = { days }
      if (platform) params.platform = platform

      let res, filename
      if (type === 'csv') {
        res = await exportAPI.csv(params)
        filename = `ecomsight_reviews_${new Date().toISOString().slice(0,10)}.csv`
      } else if (type === 'excel') {
        res = await exportAPI.excel(params)
        filename = `ecomsight_bao_cao_${new Date().toISOString().slice(0,10)}.xlsx`
      } else {
        res = await exportAPI.pdf(params)
        filename = `ecomsight_bao_cao_${new Date().toISOString().slice(0,10)}.pdf`
      }

      downloadBlob(res.data, filename)
    } catch (e) {
      alert(`❌ Lỗi xuất file: ${e.response?.data?.detail || e.message}`)
    } finally {
      setLoadingId(null)
    }
  }

  return (
    <div>
      <Header title="Xuất Báo cáo" subtitle="Tải về dữ liệu phân tích theo nhiều định dạng" />
      <div className="page-content">

        {/* Filters */}
        <div className="card mb-6">
          <div className="card-title mb-4">⚙️ Tùy chọn xuất</div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div className="input-group" style={{ flex: 1, minWidth: 200 }}>
              <label className="input-label">Khoảng thời gian</label>
              <select className="input" value={days} onChange={e => setDays(Number(e.target.value))}>
                <option value={7}>7 ngày qua</option>
                <option value={30}>30 ngày qua</option>
                <option value={90}>90 ngày qua</option>
                <option value={180}>6 tháng qua</option>
                <option value={365}>1 năm qua</option>
              </select>
            </div>
            <div className="input-group" style={{ flex: 1, minWidth: 200 }}>
              <label className="input-label">Nền tảng</label>
              <select className="input" value={platform} onChange={e => setPlatform(e.target.value)}>
                <option value="">Tất cả</option>
                <option value="shopee">🛍️ Shopee</option>
                <option value="tiktok">🎵 TikTok</option>
              </select>
            </div>
          </div>
        </div>

        {/* Export Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {EXPORT_OPTIONS.map(opt => {
            const Icon = opt.icon
            const isLoading = loadingId === opt.id
            return (
              <div key={opt.id} className={`kpi-card ${opt.color}`} style={{ cursor: 'default' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                  <div className={`kpi-icon ${opt.color}`} style={{ flexShrink: 0 }}>
                    <Icon size={22} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)', marginBottom: 6 }}>
                      {opt.title}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 16 }}>
                      {opt.desc}
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleExport(opt.id)}
                      disabled={isLoading}
                      style={{ width: '100%', justifyContent: 'center' }}
                    >
                      {isLoading
                        ? <><div className="spinner" style={{ width: 15, height: 15 }} /> Đang xuất...</>
                        : <><Download size={15} /> Tải xuống {opt.ext}</>
                      }
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Note */}
        <div style={{
          marginTop: 24,
          padding: '16px 20px',
          background: 'var(--primary-50)',
          border: '1px solid var(--primary-200)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.82rem',
          color: 'var(--primary-800)',
        }}>
          <strong>💡 Tip:</strong> File CSV là định dạng tốt nhất để gán nhãn thủ công.
          Sau khi gán nhãn xong, import lại bằng tính năng "Import CSV" ở trang Đánh giá,
          rồi dùng file đã gán nhãn để fine-tune model PhoBERT trên Google Colab.
        </div>
      </div>
    </div>
  )
}
