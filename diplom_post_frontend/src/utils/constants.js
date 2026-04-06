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
  sorting_center_worker: 'Працівник сортувального центру',
  distribution_center_worker: 'Працівник розподільчого центру',
  logist: 'Логіст',
  driver: 'Водій',
  hr: 'HR',
  admin: 'Адміністратор',
}

export const WORKER_ROLES = [
  'postal_worker',
  'sorting_center_worker',
  'distribution_center_worker',
  'driver',
  'logist',
  'hr',
]

export const WAREHOUSE_ROLES = [
  'sorting_center_worker',
  'distribution_center_worker',
]

export const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/track',
]
