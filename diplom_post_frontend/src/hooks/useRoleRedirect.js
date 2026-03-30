// src/hooks/useRoleRedirect.js

import { useCallback } from 'react'

export const ROLE_HOME_ROUTES = {
  customer: '/customer/dashboard',
  postal_worker: '/postal/dashboard',
  warehouse_worker: '/warehouse/dashboard',
  logist: '/logist/dashboard',
  driver: '/driver/dashboard',
  hr: '/hr/dashboard',
  admin: '/admin/dashboard',
}

export function useRoleRedirect() {
  return useCallback((role) => ROLE_HOME_ROUTES[role] || '/login', [])
}