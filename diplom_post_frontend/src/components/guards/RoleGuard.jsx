import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import LoadingSpinner from '../common/LoadingSpinner'
import { useRoleRedirect } from '../../hooks/useRoleRedirect'

export default function RoleGuard({
  allowedRoles = [],
  redirectAuthenticated = false,
}) {
  const location = useLocation()
  const { user, accessToken, loading } = useAuthStore()
  const getHomeRoute = useRoleRedirect()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  // Public auth routes: /login, /register
  // Редіректимо тільки якщо роль справді відома
  if (redirectAuthenticated) {
    if (accessToken && user?.role) {
      const homeRoute = getHomeRoute(user.role)

      // Захист від циклу /login -> /login
      if (homeRoute && homeRoute !== location.pathname) {
        return <Navigate to={homeRoute} replace />
      }
    }

    return <Outlet />
  }

  // Private routes
  if (!accessToken || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />
  }

  return <Outlet />
}