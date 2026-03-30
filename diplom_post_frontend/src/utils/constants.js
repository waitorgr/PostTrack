// src/utils/constants.js

export const APP_NAME = 'Diplom Post'

export const DEFAULT_PAGE_SIZE = 20
export const DEFAULT_PAGE = 1

export const LOCAL_STORAGE_KEYS = {
  ACCESS_TOKEN: 'accessToken',
  REFRESH_TOKEN: 'refreshToken',
}

export const ROLE_LABELS = {
  customer: 'Клієнт',
  postal_worker: 'Працівник відділення',
  warehouse_worker: 'Працівник складу',
  logist: 'Логіст',
  driver: 'Водій',
  hr: 'HR',
  admin: 'Адміністратор',
}

export const WORKER_ROLES = [
  'postal_worker',
  'warehouse_worker',
  'driver',
  'logist',
  'hr',
]

export const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/track',
]