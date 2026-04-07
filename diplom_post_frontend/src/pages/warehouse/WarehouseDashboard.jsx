import { Box, Typography } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import ShipmentTable from '../../components/domain/ShipmentTable'
import { useShipments } from '../../hooks/useShipments'
import Button from '../../components/ui/Button'
import { apiDownloadLocationReport } from '../../api/reports'

export default function WarehouseDashboard() {
  const { data, isLoading, isError, refetch } = useShipments({ page_size: 8 })

  const shipments = data?.results || data || []

  const locationReportMutation = useMutation({
    mutationFn: apiDownloadLocationReport,
  })

  const arrived = shipments.filter((s) => s.status === 'arrived_at_facility').length
  const sorted = shipments.filter((s) => s.status === 'sorted').length
  const inTransit = shipments.filter((s) => s.status === 'in_transit').length
  const outForDelivery = shipments.filter((s) => s.status === 'out_for_delivery').length

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="Склад / сортування"
        subtitle="Огляд поточного стану вузла"
        actions={
          <Button variant="outlined" onClick={() => locationReportMutation.mutate({})} disabled={locationReportMutation.isPending}>
            Звіт по локації
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
        <StatCard title="Прибуло на вузол" value={arrived} />
        <StatCard title="Відсортовано" value={sorted} />
        <StatCard title="В дорозі" value={inTransit} />
        <StatCard title="Готово до передачі" value={outForDelivery} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          Актуальні посилки вузла
        </Typography>

        <ShipmentTable rows={shipments} loading={false} />
      </Box>
    </>
  )
}