import { create } from 'zustand'
import { apiLogin, apiLogout, apiMe } from '../api/auth'

export const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: localStorage.getItem('access') || null,
  refreshToken: localStorage.getItem('refresh') || null,
  loading: false,

  setTokens: (access, refresh) => {
    localStorage.setItem('access', access)
    localStorage.setItem('refresh', refresh)
    set({ accessToken: access, refreshToken: refresh })
  },

  clearTokens: () => {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    set({ accessToken: null, refreshToken: null, user: null })
  },

  login: async (username, password) => {
    set({ loading: true })
    try {
      const data = await apiLogin(username, password)
      get().setTokens(data.access, data.refresh)
      const user = await apiMe()
      set({ user, loading: false })
      return { ok: true }
    } catch (e) {
      set({ loading: false })
      return { ok: false, error: e.response?.data?.detail || 'Невірний логін або пароль' }
    }
  },

  logout: async () => {
    try { await apiLogout(get().refreshToken) } catch {}
    get().clearTokens()
  },

  fetchMe: async () => {
    try {
      const user = await apiMe()
      set({ user })
    } catch {
      get().clearTokens()
    }
  },
}))
