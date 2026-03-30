import { Box, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import EmptyState from '../../components/common/EmptyState'
import ShipmentCard from '../../components/domain/ShipmentCard'
import { useShipments } from '../../hooks/useShipments'

export default function CustomerDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useShipments({ page_size: 6 })

  const shipments = data?.results || data || []

  const activeStatuses = [
    'accepted',
    'picked_up_by_driver',
    'in_transit',
    'arrived_at_facility',
    'sorted',
    'out_for_delivery',
  ]

  const activeCount = shipments.filter((s) => activeStatuses.includes(s.status)).length
  const readyCount = shipments.filter((s) => s.status === 'available_for_pickup').length
  const deliveredCount = shipments.filter((s) => s.status === 'delivered').length

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="Кабінет клієнта"
        subtitle="Огляд твоїх поточних відправлень"
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
        <StatCard title="Усього посилок" value={shipments.length} />
        <StatCard title="Активні" value={activeCount} />
        <StatCard title="Готові до отримання" value={readyCount} />
        <StatCard title="Доставлені" value={deliveredCount} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          Останні посилки
        </Typography>

        {!shipments.length ? (
          <EmptyState
            title="Посилок поки немає"
            description="Коли з’являться відправлення, ти побачиш їх тут."
          />
        ) : (
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: {
                xs: '1fr',
                md: 'repeat(2, 1fr)',
              },
            }}
          >
            {shipments.map((shipment) => (
              <ShipmentCard
                key={shipment.id}
                shipment={shipment}
                actionLabel="Відкрити"
                onAction={(item) => navigate(`/customer/shipments/${item.id}`)}
              />
            ))}
          </Box>
        )}
      </Box>
    </>
  )
}