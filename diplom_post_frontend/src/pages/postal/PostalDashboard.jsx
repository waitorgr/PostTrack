import { Box, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import ShipmentTable from '../../components/domain/ShipmentTable'
import { useShipments } from '../../hooks/useShipments'

export default function PostalDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useShipments({
    page_size: 8,
    only_current_location: true,
  })

  const shipments = data?.results || data || []
  const today = dayjs().format('YYYY-MM-DD')

  const createdToday = shipments.filter(
    (s) => s.created_at && dayjs(s.created_at).format('YYYY-MM-DD') === today
  ).length

  const readyForPickup = shipments.filter((s) => s.status === 'available_for_pickup').length
  const inProcessing = shipments.filter((s) =>
    ['accepted', 'sorted', 'out_for_delivery'].includes(s.status)
  ).length
  const delivered = shipments.filter((s) => s.status === 'delivered').length

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="Робоче місце відділення"
        subtitle="Оперативний огляд відділення"
        actions={
          <Button onClick={() => navigate('/postal/shipments/create')}>
            Створити посилку
          </Button>
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
        <StatCard title="Створено сьогодні" value={createdToday} />
        <StatCard title="В обробці" value={inProcessing} />
        <StatCard title="Очікують видачі" value={readyForPickup} />
        <StatCard title="Доставлено" value={delivered} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          Останні посилки
        </Typography>

        <ShipmentTable
          rows={shipments}
          loading={false}
          onRowClick={(row) => navigate(`/postal/shipments/${row.id}`)}
        />
      </Box>
    </>
  )
}