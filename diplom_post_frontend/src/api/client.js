import axios from 'axios'
import { LOCAL_STORAGE_KEYS } from '../utils/constants'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
})

const getAccessToken = () => localStorage.getItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)
const getRefreshToken = () => localStorage.getItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN)

const setTokens = ({ access, refresh }) => {
  if (access) localStorage.setItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, access)
  if (refresh) localStorage.setItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN, refresh)
}

const clearTokens = () => {
  localStorage.removeItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)
  localStorage.removeItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN)
}

client.interceptors.request.use(
  (config) => {
    const token = getAccessToken()

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

let refreshPromise = null

const refreshAccessToken = async () => {
  const refresh = getRefreshToken()
  if (!refresh) {
    throw new Error('No refresh token')
  }

  const response = await axios.post(`${BASE_URL}/accounts/token/refresh/`, {
    refresh,
  })

  setTokens(response.data)
  return response.data.access
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    const isUnauthorized = error.response?.status === 401
    const isLoginRequest = originalRequest?.url?.includes('/accounts/login/')
    const isRefreshRequest = originalRequest?.url?.includes('/accounts/token/refresh/')

    if (!isUnauthorized || originalRequest?._retry || isLoginRequest || isRefreshRequest) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }

      const newAccessToken = await refreshPromise
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`

      return client(originalRequest)
    } catch (refreshError) {
      clearTokens()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    }
  }
)

export default client