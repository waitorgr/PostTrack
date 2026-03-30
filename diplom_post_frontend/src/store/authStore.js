import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { apiLogin, apiLogout, apiMe } from '../api/auth'
import { LOCAL_STORAGE_KEYS } from '../utils/constants'

const AUTH_STORE_NAME = 'auth-storage'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: localStorage.getItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN) || null,
      refreshToken: localStorage.getItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN) || null,
      loading: false,

      setTokens: (access, refresh) => {
        if (access) {
          localStorage.setItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, access)
        }
        if (refresh) {
          localStorage.setItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN, refresh)
        }

        set({
          accessToken: access || null,
          refreshToken: refresh || null,
        })
      },

      clearTokens: () => {
        localStorage.removeItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN)

        set({
          accessToken: null,
          refreshToken: null,
          user: null,
        })
      },

      login: async (username, password) => {
        set({ loading: true })

        try {
          const data = await apiLogin(username, password)

          get().setTokens(data.access, data.refresh)

          const user = await apiMe()

          set({
            user,
            loading: false,
          })

          return { ok: true, user }
        } catch (error) {
          set({ loading: false })

          const backendError =
            error.response?.data?.detail ||
            Object.values(error.response?.data || {}).flat().join(' ') ||
            'Невірний логін або пароль'

          return { ok: false, error: backendError }
        }
      },

      logout: async () => {
        const refresh = get().refreshToken

        try {
          if (refresh) {
            await apiLogout(refresh)
          }
        } catch {
          // нічого, локально все одно чистимо
        } finally {
          get().clearTokens()
        }
      },

      fetchMe: async () => {
        const token = get().accessToken
        if (!token) return null

        try {
          const user = await apiMe()
          set({ user })
          return user
        } catch {
          get().clearTokens()
          return null
        }
      },
    }),
    {
      name: AUTH_STORE_NAME,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)