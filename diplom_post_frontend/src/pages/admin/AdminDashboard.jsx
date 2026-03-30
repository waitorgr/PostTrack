import { Box, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import { useShipments } from '../../hooks/useShipments'
import { useRoutes } from '../../hooks/useRoutes'
import { useUsers } from '../../hooks/useUsers'
import { apiGetLocations } from '../../api/locations'

export default function AdminDashboard() {
  const navigate = useNavigate()

  const shipmentsQuery = useShipments({ page_size: 5 })
  const routesQuery = useRoutes({ page_size: 5 })
  const usersQuery = useUsers({ page_size: 5 })

  const locationsQuery = useQuery({
    queryKey: ['locations', 'dashboard'],
    queryFn: () => apiGetLocations({ page_size: 5 }),
  })

  const isLoading =
    shipmentsQuery.isLoading ||
    routesQuery.isLoading ||
    usersQuery.isLoading ||
    locationsQuery.isLoading

  const isError =
    shipmentsQuery.isError ||
    routesQuery.isError ||
    usersQuery.isError ||
    locationsQuery.isError

  if (isLoading) return <LoadingSpinner />
  if (isError) {
    return (
      <ErrorState
        onRetry={() => {
          shipmentsQuery.refetch()
          routesQuery.refetch()
          usersQuery.refetch()
          locationsQuery.refetch()
        }}
      />
    )
  }

  const shipments = shipmentsQuery.data?.results || shipmentsQuery.data || []
  const routes = routesQuery.data?.results || routesQuery.data || []
  const users = usersQuery.data?.results || usersQuery.data || []
  const locations = locationsQuery.data?.results || locationsQuery.data || []

  return (
    <>
      <PageHeader
        title="Адміністративна панель"
        subtitle="Загальний огляд системи"
        actions={
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button onClick={() => navigate('/admin/shipments')}>Посилки</Button>
            <Button onClick={() => navigate('/admin/users')}>Користувачі</Button>
            <Button onClick={() => navigate('/admin/routes')}>Маршрути</Button>
          </Box>
        }
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            lg: 'repeat(4, 1fr)',
          },
        }}
      >
        <StatCard title="Посилки" value={shipments.length} />
        <StatCard title="Маршрути" value={routes.length} />
        <StatCard title="Користувачі" value={users.length} />
        <StatCard title="Локації" value={locations.length} />
      </Box>

      <Box
        sx={{
          mt: 4,
          display: 'grid',
          gap: 3,
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'repeat(3, 1fr)',
          },
        }}
      >
        <Box
          sx={{
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 3,
            backgroundColor: 'background.paper',
          }}
        >
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Останні посилки
          </Typography>
          {shipments.map((item) => (
            <Typography key={item.id} variant="body2" sx={{ mb: 1 }}>
              {item.tracking_number || `#${item.id}`}
            </Typography>
          ))}
        </Box>

        <Box
          sx={{
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 3,
            backgroundColor: 'background.paper',
          }}
        >
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Останні маршрути
          </Typography>
          {routes.map((item) => (
            <Typography key={item.id} variant="body2" sx={{ mb: 1 }}>
              {item.name || item.code || `Маршрут #${item.id}`}
            </Typography>
          ))}
        </Box>

        <Box
          sx={{
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 3,
            backgroundColor: 'background.paper',
          }}
        >
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Останні користувачі
          </Typography>
          {users.map((item) => (
            <Typography key={item.id} variant="body2" sx={{ mb: 1 }}>
              {item.username || `Користувач #${item.id}`}
            </Typography>
          ))}
        </Box>
      </Box>
    </>
  )
}