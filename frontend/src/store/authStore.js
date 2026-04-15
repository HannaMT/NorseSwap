import { create } from 'zustand'
import { authApi } from '../api/client'

const useAuthStore = create((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  init: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return set({ isLoading: false })
    try {
      const { data } = await authApi.me()
      set({ user: data, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ isLoading: false })
    }
  },

  login: (tokens, user) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    set({ user, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  updateUser: (updates) => set((s) => ({ user: { ...s.user, ...updates } })),
}))

export default useAuthStore