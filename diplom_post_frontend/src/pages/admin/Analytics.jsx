import { Box, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import Card from '../../components/ui/Card'
import { useShipments } from '../../hooks/useShipments'
import { useRoutes } from '../../hooks/useRoutes'
import { useUsers } from '../../hooks/useUsers'
import { apiGetLocations } from '../../api/locations'
import { SHIPMENT_STATUS_LABELS } from '../../utils/statusConfig'

export default function Analytics() {
  const shipmentsQuery = useShipments({ page_size: 100 })
  const routesQuery = useRoutes({ page_size: 100 })
  const usersQuery = useUsers({ page_size: 100 })

  const locationsQuery = useQuery({
    queryKey: ['analytics', 'locations'],
    queryFn: () => apiGetLocations({ page_size: 100 }),
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

  const deliveredShipments = shipments.filter((s) => s.status === 'delivered').length
  const activeShipments = shipments.filter((s) =>
    ['accepted', 'picked_up_by_driver', 'in_transit', 'arrived_at_facility', 'sorted', 'out_for_delivery'].includes(s.status)
  ).length
  const readyForPickup = shipments.filter((s) => s.status === 'available_for_pickup').length
  const cancelledShipments = shipments.filter((s) => s.status === 'cancelled').length

  const inProgressRoutes = routes.filter((r) => r.status === 'in_progress').length
  const completedRoutes = routes.filter((r) => r.status === 'completed').length

  const roleStats = users.reduce((acc, user) => {
    const key = user.role || 'unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})

  const shipmentStatusStats = shipments.reduce((acc, item) => {
    const key = item.status || 'unknown'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})

  return (
    <>
      <PageHeader
        title="Аналітика"
        subtitle="Зведені показники системи"
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            xl: 'repeat(4, 1fr)',
          },
        }}
      >
        <StatCard title="Усього посилок" value={shipments.length} />
        <StatCard title="Активні посилки" value={activeShipments} />
        <StatCard title="Доставлені посилки" value={deliveredShipments} />
        <StatCard title="Очікують отримання" value={readyForPickup} />
        <StatCard title="Скасовані посилки" value={cancelledShipments} />
        <StatCard title="Усього маршрутів" value={routes.length} />
        <StatCard title="Маршрути в роботі" value={inProgressRoutes} />
        <StatCard title="Завершені маршрути" value={completedRoutes} />
        <StatCard title="Усього користувачів" value={users.length} />
        <StatCard title="Усього локацій" value={locations.length} />
      </Box>

      <Box
        sx={{
          mt: 4,
          display: 'grid',
          gap: 3,
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'repeat(2, 1fr)',
          },
        }}
      >
        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Розподіл користувачів по ролях
          </Typography>

          <Stack spacing={1}>
            {Object.entries(roleStats).map(([role, count]) => (
              <Box
                key={role}
                sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}
              >
                <Typography>{role}</Typography>
                <Typography fontWeight={700}>{count}</Typography>
              </Box>
            ))}
          </Stack>
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Розподіл посилок по статусах
          </Typography>

          <Stack spacing={1}>
            {Object.entries(shipmentStatusStats).map(([status, count]) => (
              <Box
                key={status}
                sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}
              >
                <Typography>
                  {SHIPMENT_STATUS_LABELS[status] || status}
                </Typography>
                <Typography fontWeight={700}>{count}</Typography>
              </Box>
            ))}
          </Stack>
        </Card>
      </Box>
    </>
  )
}