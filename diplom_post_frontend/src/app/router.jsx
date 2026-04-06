import React, { Suspense, lazy } from 'react'
import { createBrowserRouter, Navigate, useParams } from 'react-router-dom'

import PublicLayout from '../layouts/PublicLayout'
import CustomerLayout from '../layouts/CustomerLayout'
import InternalLayout from '../layouts/InternalLayout'
import DriverLayout from '../layouts/DriverLayout'
import AdminLayout from '../layouts/AdminLayout'

import RoleGuard from '../components/guards/RoleGuard'
import LoadingSpinner from '../components/common/LoadingSpinner'

const LogistDispatchDetails = lazy(() => import('../pages/logist/DispatchDetails'))
const LandingPage = lazy(() => import('../pages/public/LandingPage'))
const LoginPage = lazy(() => import('../pages/public/LoginPage'))
const RegisterPage = lazy(() => import('../pages/public/RegisterPage'))
const PublicTrackingPage = lazy(() => import('../pages/public/PublicTrackingPage'))
const TrackingResultPage = lazy(() => import('../pages/public/TrackingResultPage'))

const CustomerDashboard = lazy(() => import('../pages/customer/CustomerDashboard'))
const CustomerShipments = lazy(() => import('../pages/customer/CustomerShipments'))
const CustomerShipmentDetails = lazy(() => import('../pages/customer/ShipmentDetails'))

const PostalDashboard = lazy(() => import('../pages/postal/PostalDashboard'))
const ShipmentList = lazy(() => import('../pages/postal/ShipmentList'))
const ShipmentCreate = lazy(() => import('../pages/postal/ShipmentCreate'))
const ShipmentDetails = lazy(() => import('../pages/postal/ShipmentDetails'))
const DispatchList = lazy(() => import('../pages/postal/DispatchList'))
const DispatchDetails = lazy(() => import('../pages/postal/DispatchDetails'))

const WarehouseDashboard = lazy(() => import('../pages/warehouse/WarehouseDashboard'))
const IncomingGroups = lazy(() => import('../pages/warehouse/IncomingGroups'))
const WarehouseParcels = lazy(() => import('../pages/warehouse/WarehouseParcels'))
const SortingInterface = lazy(() => import('../pages/warehouse/SortingInterface'))
const WarehouseDispatchDetails = lazy(() => import('../pages/postal/DispatchDetails'))

const LogistDashboard = lazy(() => import('../pages/logist/LogistDashboard'))
const RouteList = lazy(() => import('../pages/logist/RouteList'))
const RouteCreate = lazy(() => import('../pages/logist/RouteCreate'))
const RouteDetails = lazy(() => import('../pages/logist/RouteDetails'))
const DispatchOverview = lazy(() => import('../pages/logist/DispatchOverview'))
const NodesOverview = lazy(() => import('../pages/logist/NodesOverview'))

const DriverDashboard = lazy(() => import('../pages/driver/DriverDashboard'))
const DriverRoutes = lazy(() => import('../pages/driver/DriverRoutes'))
const RouteExecution = lazy(() => import('../pages/driver/RouteExecution'))

const HRDashboard = lazy(() => import('../pages/hr/HRDashboard'))
const UserList = lazy(() => import('../pages/hr/UserList'))
const UserCreate = lazy(() => import('../pages/hr/UserCreate'))
const UserEdit = lazy(() => import('../pages/hr/UserEdit'))
const LocationsList = lazy(() => import('../pages/hr/LocationsList'))

const AdminDashboard = lazy(() => import('../pages/admin/AdminDashboard'))
const AdminShipments = lazy(() => import('../pages/admin/AdminShipments'))
const AdminUsers = lazy(() => import('../pages/admin/AdminUsers'))
const AdminLocations = lazy(() => import('../pages/admin/AdminLocations'))
const AdminRoutes = lazy(() => import('../pages/admin/AdminRoutes'))
const Analytics = lazy(() => import('../pages/admin/Analytics'))
const SystemSettings = lazy(() => import('../pages/admin/SystemSettings'))

const UnauthorizedPage = lazy(() => import('../pages/errors/UnauthorizedPage'))
const NotFoundPage = lazy(() => import('../pages/errors/NotFoundPage'))


function LegacyPostalDispatchRedirect() {
  const { id } = useParams()
  return <Navigate to={id ? `/postal/dispatch/${id}` : '/postal/dispatch'} replace />
}

function withSuspense(element) {
  return (
    <Suspense fallback={<LoadingSpinner minHeight={320} />}>
      {element}
    </Suspense>
  )
}

export const router = createBrowserRouter([

  {
    path: '/dispatch/groups',
    element: <Navigate to="/postal/dispatch" replace />,
  },
  {
    path: '/dispatch/groups/:id',
    element: <LegacyPostalDispatchRedirect />,
  },

  {
    path: '/',
    element: <PublicLayout />,
    children: [
      { index: true, element: withSuspense(<LandingPage />) },
      {
        element: <RoleGuard redirectAuthenticated />,
        children: [
          { path: 'login', element: withSuspense(<LoginPage />) },
          { path: 'register', element: withSuspense(<RegisterPage />) },
        ],
      },
      { path: 'track', element: withSuspense(<PublicTrackingPage />) },
      { path: 'track/:trackingCode', element: withSuspense(<TrackingResultPage />) },
    ],
  },

  {
    path: '/customer',
    element: <RoleGuard allowedRoles={['customer', 'admin']} />,
    children: [
      {
        element: <CustomerLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<CustomerDashboard />) },
          { path: 'shipments', element: withSuspense(<CustomerShipments />) },
          { path: 'shipments/:id', element: withSuspense(<CustomerShipmentDetails />) },
        ],
      },
    ],
  },

  {
    path: '/postal',
    element: <RoleGuard allowedRoles={['postal_worker', 'admin']} />,
    children: [
      {
        element: <InternalLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<PostalDashboard />) },
          { path: 'shipments', element: withSuspense(<ShipmentList />) },
          { path: 'shipments/create', element: withSuspense(<ShipmentCreate />) },
          { path: 'shipments/:id', element: withSuspense(<ShipmentDetails />) },
          { path: 'dispatch', element: withSuspense(<DispatchList />) },
          { path: 'dispatch/:id', element: withSuspense(<DispatchDetails />) },
        ],
      },
    ],
  },

  {
    path: '/warehouse',
    element: <RoleGuard allowedRoles={['sorting_center_worker', 'distribution_center_worker', 'admin']} />,
    children: [
      {
        element: <InternalLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<WarehouseDashboard />) },
          { path: 'incoming', element: withSuspense(<IncomingGroups />) },
          { path: 'parcels', element: withSuspense(<WarehouseParcels />) },
          { path: 'sorting', element: withSuspense(<SortingInterface />) },
          { path: 'dispatch/:id', element: withSuspense(<WarehouseDispatchDetails />) },
        ],
      },
    ],
  },

  {
    path: '/logist',
    element: <RoleGuard allowedRoles={['logist', 'admin']} />,
    children: [
      {
        element: <InternalLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<LogistDashboard />) },
          { path: 'routes', element: withSuspense(<RouteList />) },
          { path: 'routes/create', element: withSuspense(<RouteCreate />) },
          { path: 'routes/:id', element: withSuspense(<RouteDetails />) },
          { path: 'dispatches', element: withSuspense(<DispatchOverview />) },
          { path: 'nodes', element: withSuspense(<NodesOverview />) },
          { path: 'dispatches/:id', element: withSuspense(<LogistDispatchDetails />) },
        ],
      },
    ],
  },

  {
    path: '/driver',
    element: <RoleGuard allowedRoles={['driver', 'admin']} />,
    children: [
      {
        element: <DriverLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<DriverDashboard />) },
          { path: 'routes', element: withSuspense(<DriverRoutes />) },
          { path: 'routes/:id', element: withSuspense(<RouteExecution />) },
        ],
      },
    ],
  },

  {
    path: '/hr',
    element: <RoleGuard allowedRoles={['hr', 'admin']} />,
    children: [
      {
        element: <InternalLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<HRDashboard />) },
          { path: 'users', element: withSuspense(<UserList />) },
          { path: 'users/create', element: withSuspense(<UserCreate />) },
          { path: 'users/:id/edit', element: withSuspense(<UserEdit />) },
          { path: 'locations', element: withSuspense(<LocationsList />) },
        ],
      },
    ],
  },

  {
    path: '/admin',
    element: <RoleGuard allowedRoles={['admin']} />,
    children: [
      {
        element: <AdminLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: withSuspense(<AdminDashboard />) },
          { path: 'shipments', element: withSuspense(<AdminShipments />) },
          { path: 'users', element: withSuspense(<AdminUsers />) },
          { path: 'locations', element: withSuspense(<AdminLocations />) },
          { path: 'routes', element: withSuspense(<AdminRoutes />) },
          { path: 'analytics', element: withSuspense(<Analytics />) },
          { path: 'settings', element: withSuspense(<SystemSettings />) },
        ],
      },
    ],
  },

  {
    path: '/unauthorized',
    element: withSuspense(<UnauthorizedPage />),
  },

  {
    path: '*',
    element: withSuspense(<NotFoundPage />),
  },
])