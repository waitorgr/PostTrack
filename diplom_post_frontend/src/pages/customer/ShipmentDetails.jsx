import { Box, Divider, Stack, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import TrackingTimeline from '../../components/domain/TrackingTimeline'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { useShipment } from '../../hooks/useShipments'
import { fDateTime } from '../../utils/formatters'

export default function ShipmentDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: shipment, isLoading, isError, refetch } = useShipment(id)

  if (isLoading) return <LoadingSpinner />
  if (isError || !shipment) return <ErrorState onRetry={refetch} />

  const trackingEvents = shipment.tracking_events || shipment.events || []

  return (
    <>
      <PageHeader
        title={shipment.tracking_number || `Посилка #${shipment.id}`}
        subtitle="Детальна інформація про відправлення"
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Button variant="text" onClick={() => navigate('/customer/shipments')}>
              Назад
            </Button>
            {shipment.tracking_number && (
              <Button
                variant="outlined"
                onClick={() => navigate(`/track/${shipment.tracking_number}`)}
              >
                Публічний трекінг
              </Button>
            )}
          </Stack>
        }
      />

      <Stack spacing={3}>
        <Card>
          <Stack spacing={2}>
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems={{ xs: 'flex-start', sm: 'center' }}
              flexDirection={{ xs: 'column', sm: 'row' }}
              gap={2}
            >
              <Typography variant="h6" fontWeight={700}>
                Загальна інформація
              </Typography>
              <StatusBadge status={shipment.status} type="shipment" />
            </Box>

            <Divider />

            <Stack spacing={1}>
              <Typography>
                <strong>Трек-номер:</strong> {shipment.tracking_number || '—'}
              </Typography>
              <Typography>
                <strong>Опис:</strong> {shipment.description || '—'}
              </Typography>
              <Typography>
                <strong>Створено:</strong> {fDateTime(shipment.created_at)}
              </Typography>
              <Typography>
                <strong>Відправник:</strong> {shipment.sender_name || '—'}
              </Typography>
              <Typography>
                <strong>Отримувач:</strong> {shipment.recipient_name || '—'}
              </Typography>
              <Typography>
                <strong>Звідки:</strong> {shipment.origin?.name || shipment.origin_name || '—'}
              </Typography>
              <Typography>
                <strong>Куди:</strong> {shipment.destination?.name || shipment.destination_name || '—'}
              </Typography>
              <Typography>
                <strong>Тип оплати:</strong> {shipment.payment_type || '—'}
              </Typography>
            </Stack>
          </Stack>
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Історія руху
          </Typography>

          <TrackingTimeline events={trackingEvents} />
        </Card>
      </Stack>
    </>
  )
}