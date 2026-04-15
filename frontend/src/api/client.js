import axios from 'axios'
import toast from 'react-hot-toast'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

const cleanParams = (params) =>
  Object.fromEntries(
    Object.entries(params || {}).filter(
      ([, v]) => v !== '' && v !== null && v !== undefined,
    ),
  )

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle token expiry — refresh automatically
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config

    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) throw new Error('No refresh token')

        const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh })
        localStorage.setItem('access_token', data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }

    // Show error toast for non-401s
    const message = err.response?.data?.detail || 'Something went wrong'
    if (err.response?.status !== 401) toast.error(message)

    return Promise.reject(err)
  },
)

export default api

// ─── API helpers ──────────────────────────────

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),
}

export const listingsApi = {
  getAll: (params) => api.get('/listings', { params: cleanParams(params) }),
  getOne: (id) => api.get(`/listings/${id}`),
  getMine: (params) => api.get('/listings/me', { params: cleanParams(params) }),
  create: (formData) => api.post('/listings', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  update: (id, data) => api.patch(`/listings/${id}`, data),
  delete: (id) => api.delete(`/listings/${id}`),
  toggleSave: (id) => api.post(`/listings/${id}/save`),
}

export const rentalsApi = {
  request: (data) => api.post('/rentals', data),
  getMyRentals: (params) => api.get('/rentals/my-rentals', { params: cleanParams(params) }),
  getMyLendings: (params) => api.get('/rentals/my-lendings', { params: cleanParams(params) }),
  respond: (id, action) => api.patch(`/rentals/${id}/respond`, { action }),
  markReturned: (id, data) => api.patch(`/rentals/${id}/return`, data),
  cancel: (id) => api.patch(`/rentals/${id}/cancel`),
}

export const ordersApi = {
  create: (data) => api.post('/orders', data),
  getMyOrders: (params) => api.get('/orders/my-orders', { params: cleanParams(params) }),
  getMySales: (params) => api.get('/orders/my-sales', { params: cleanParams(params) }),
  scheduleMeetup: (id, data) =>
    api.patch(`/orders/${id}/schedule-meetup`, null, { params: cleanParams(data) }),
  complete: (id) => api.patch(`/orders/${id}/complete`),
  cancel: (id) => api.patch(`/orders/${id}/cancel`),
}

export const servicesApi = {
  createBooking: (data) => api.post('/services/bookings', data),
  getMyBookings: (params) => api.get('/services/my-bookings', { params: cleanParams(params) }),
  getMyServices: (params) => api.get('/services/my-services', { params: cleanParams(params) }),
  confirm: (id) => api.patch(`/services/${id}/confirm`),
  complete: (id) => api.patch(`/services/${id}/complete`),
  cancel: (id) => api.patch(`/services/${id}/cancel`),
}

export const messagesApi = {
  getConversations: () => api.get('/messages/conversations'),
  getMessages: (convId) => api.get(`/messages/conversations/${convId}/messages`),
  createConversation: (data) => api.post('/messages/conversations', data),
}

export const reviewsApi = {
  create: (data) => api.post('/reviews', data),
  getUserReviews: (userId) => api.get(`/reviews/user/${userId}`),
}

export const notificationsApi = {
  getAll: () => api.get('/notifications'),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAllRead: () => api.patch('/notifications/read-all'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
}

export const usersApi = {
  getProfile: (id) => api.get(`/users/${id}`),
  updateMe: (data) => api.patch('/users/me', data),
  uploadAvatar: (formData) => api.post('/users/me/avatar', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getSaved: () => api.get('/users/me/saved'),
}

export const paymentsApi = {
  createIntent: (data) => api.post('/payments/intent', data),
  connectStripe: () => api.post('/payments/connect'),
  getConnectStatus: () => api.get('/payments/connect/status'),
}