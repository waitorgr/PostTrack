import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { CircularProgress, Box } from '@mui/material'

import AppLayout from './components/layout/AppLayout'
import PrivateRoute from './components/layout/PrivateRoute'

import Login from './pages/Login'
import Register from './pages/Register'
import PublicTracking from './pages/PublicTracking'
import Dashboard from './pages/Dashboard'
import ShipmentList from './pages/shipments/ShipmentList'
import ShipmentCreate from './pages/shipments/ShipmentCreate'
import ShipmentDetail from './pages/shipments/ShipmentDetail'
import DispatchList from './pages/dispatch/DispatchList'
import RouteList from './pages/logistics/RouteList'
import ChatPage from './pages/chat/ChatPage'
import ReportsPage from './pages/reports/ReportsPage'
import UsersPage from './pages/hr/UsersPage'
import MyShipments from './pages/customer/MyShipments'

export default function App() {
  const { accessToken, user, fetchMe } = useAuthStore()

  useEffect(() => {
    if (accessToken && !user) fetchMe()
  }, [accessToken])

  if (accessToken && !user) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      <CircularProgress />
    </Box>
  }

  return (
    <Routes>
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/track"    element={<PublicTracking />} />

      <Route element={<PrivateRoute><AppLayout /></PrivateRoute>}>
        <Route index element={<Dashboard />} />

        <Route path="/shipments" element={
          <PrivateRoute roles={['postal_worker','warehouse_worker','logist','admin']}>
            <ShipmentList />
          </PrivateRoute>
        } />
        <Route path="/shipments/new" element={
          <PrivateRoute roles={['postal_worker','admin']}>
            <ShipmentCreate />
          </PrivateRoute>
        } />
        <Route path="/shipments/:id" element={
          <PrivateRoute roles={['postal_worker','warehouse_worker','logist','admin']}>
            <ShipmentDetail />
          </PrivateRoute>
        } />

        <Route path="/dispatch" element={
          <PrivateRoute roles={['postal_worker','warehouse_worker','admin']}>
            <DispatchList />
          </PrivateRoute>
        } />

        <Route path="/routes" element={
          <PrivateRoute roles={['logist','driver','admin']}>
            <RouteList />
          </PrivateRoute>
        } />

        <Route path="/chat" element={
          <PrivateRoute roles={['logist','driver','admin']}>
            <ChatPage />
          </PrivateRoute>
        } />

        <Route path="/reports" element={
          <PrivateRoute roles={['postal_worker','warehouse_worker','logist','admin']}>
            <ReportsPage />
          </PrivateRoute>
        } />

        <Route path="/users" element={
          <PrivateRoute roles={['hr','admin']}>
            <UsersPage />
          </PrivateRoute>
        } />

        <Route path="/my-shipments" element={
          <PrivateRoute roles={['customer']}>
            <MyShipments />
          </PrivateRoute>
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
