import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({ baseURL: API_BASE })

// Auto-attach JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authAPI = {
  login:    (username, password) => api.post('/auth/login', new URLSearchParams({ username, password })),
  register: (data)               => api.post('/auth/register', data),
  me:       ()                   => api.get('/auth/me'),
  update:   (data)               => api.put('/auth/settings', data),
}

export const reviewsAPI = {
  list:      (params) => api.get('/reviews', { params }),
  create:    (data)   => api.post('/reviews', data),
  update:    (id, data) => api.put(`/reviews/${id}`, data),
  remove:    (id)     => api.delete(`/reviews/${id}`),
  importCSV: (file)   => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/reviews/import-csv', form)
  },
}

export const analyticsAPI = {
  overview:    (params) => api.get('/analytics/overview', { params }),
  trend:       (params) => api.get('/analytics/trend', { params }),
  aspects:     (params) => api.get('/analytics/aspects', { params }),
  topProducts: (params) => api.get('/analytics/top-products', { params }),
  keywords:    (params) => api.get('/analytics/keywords', { params }),
}

export const alertsAPI = {
  list:       (params) => api.get('/alerts', { params }),
  markRead:   (id)     => api.put(`/alerts/${id}/read`),
  markAllRead: ()      => api.put('/alerts/read-all'),
  remove:     (id)     => api.delete(`/alerts/${id}`),
}

export const analysisAPI = {
  analyzeText: (data)  => api.post('/analysis/text', data),
  analyzeURL:  (data)  => api.post('/analysis/url', data),
}

export const exportAPI = {
  csv:   (params) => api.get('/export/csv',   { params, responseType: 'blob' }),
  excel: (params) => api.get('/export/excel', { params, responseType: 'blob' }),
  pdf:   (params) => api.get('/export/pdf',   { params, responseType: 'blob' }),
}

export const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default api
