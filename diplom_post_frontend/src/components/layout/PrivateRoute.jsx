import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export default function PrivateRoute({ children, roles }) {
  const { user, accessToken } = useAuthStore()
  if (!accessToken) return <Navigate to="/login" replace />
  if (!user) return null
  if (roles && !roles.includes(user.role) && user.role !== 'admin') {
    return <Navigate to="/" replace />
  }
  return children
}
