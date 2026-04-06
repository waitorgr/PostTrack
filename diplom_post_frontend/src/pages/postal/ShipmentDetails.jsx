import { useState } from 'react'
import { Alert, Box, Chip, Divider, Stack, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import TrackingTimeline from '../../components/domain/TrackingTimeline'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import {
  useShipment,
  useCancelShipment,
  useConfirmShipmentDelivery,
  useConfirmShipmentPayment,
  useUpdateShipmentStatus,
} from '../../hooks/useShipments'
import { fDateTime } from '../../utils/formatters'

export default function ShipmentDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: shipment, isLoading, isError, refetch } = useShipment(id)

  const confirmPaymentMutation = useConfirmShipmentPayment()
  const markArrivalMutation = useUpdateShipmentStatus()
  const confirmDeliveryMutation = useConfirmShipmentDelivery()
  const cancelMutation = useCancelShipment()

  const [confirmType, setConfirmType] = useState(null)

  if (isLoading) return <LoadingSpinner />
  if (isError || !shipment) return <ErrorState onRetry={refetch} />

  const isPaid = Boolean(shipment.payment?.is_paid)
  const paymentLabel = isPaid ? 'Оплачено' : 'Не оплачено'
  const paymentColor = isPaid ? 'success' : 'warning'

  const isAtDestination =
    String(shipment.current_location_id ?? '') === String(shipment.destination ?? '') ||
    (
      shipment.current_location_name &&
      shipment.destination_name &&
      shipment.current_location_name === shipment.destination_name
    )

  const isTerminal = ['delivered', 'cancelled', 'returned'].includes(shipment.status)
  const canConfirmPayment = !isPaid && !isTerminal

  const canConfirmArrival =
    isAtDestination &&
    !isTerminal &&
    shipment.status !== 'available_for_pickup'

  const canConfirmDelivery =
    isPaid &&
    shipment.status === 'available_for_pickup' &&
    shipment.status !== 'delivered' &&
    shipment.status !== 'cancelled'

  const handleConfirmAction = async () => {
    if (confirmType === 'payment') {
      await confirmPaymentMutation.mutateAsync(shipment.id)
    }

    if (confirmType === 'arrival') {
      await markArrivalMutation.mutateAsync({
        id: shipment.id,
        status: 'available_for_pickup',
        note: 'Посилка прибула до відділення призначення та готова до видачі.',
      })
    }

    if (confirmType === 'delivery') {
      await confirmDeliveryMutation.mutateAsync(shipment.id)
    }

    if (confirmType === 'cancel') {
      await cancelMutation.mutateAsync({ id: shipment.id, reason: 'Скасовано оператором' })
    }

    setConfirmType(null)
    refetch()
  }

  const trackingEvents = shipment.tracking_events || shipment.events || []

  const senderFullName = [
    shipment.sender_last_name,
    shipment.sender_first_name,
    shipment.sender_patronymic,
  ].filter(Boolean).join(' ')

  const receiverFullName = [
    shipment.receiver_last_name,
    shipment.receiver_first_name,
    shipment.receiver_patronymic,
  ].filter(Boolean).join(' ')

  return (
    <>
      <PageHeader
        title={`Посилка ${shipment.tracking_number || `#${shipment.id}`}`}
        subtitle="Перегляд деталей та історії руху посилки"
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Button variant="text" onClick={() => navigate('/postal/shipments')}>
              Назад до списку
            </Button>

            {canConfirmPayment && (
              <Button color="warning" onClick={() => setConfirmType('payment')}>
                Підтвердити оплату
              </Button>
            )}

            {canConfirmArrival && (
              <Button color="info" onClick={() => setConfirmType('arrival')}>
                Підтвердити прибуття
              </Button>
            )}

            {canConfirmDelivery && (
              <Button color="success" onClick={() => setConfirmType('delivery')}>
                Видати отримувачу
              </Button>
            )}

            {!isTerminal && (
              <Button color="error" onClick={() => setConfirmType('cancel')}>
                Скасувати
              </Button>
            )}
          </Stack>
        }
      />

      <Stack spacing={3}>
        {(confirmPaymentMutation.isError ||
          markArrivalMutation.isError ||
          confirmDeliveryMutation.isError ||
          cancelMutation.isError) && (
          <Alert severity="error">
            Не вдалося виконати дію. Спробуй ще раз.
          </Alert>
        )}

        <Card>
          <Stack spacing={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2} flexWrap="wrap">
              <Typography variant="h6" fontWeight={700}>
                Загальна інформація
              </Typography>

              <Stack direction="row" spacing={1} flexWrap="wrap">
                <StatusBadge status={shipment.status} type="shipment" />
                <Chip
                  label={paymentLabel}
                  color={paymentColor}
                  variant="filled"
                />
              </Stack>
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
                <strong>Відправник:</strong> {senderFullName || '—'} ({shipment.sender_phone || '—'})
              </Typography>
              <Typography>
                <strong>Отримувач:</strong> {receiverFullName || '—'} ({shipment.receiver_phone || '—'})
              </Typography>
              <Typography>
                <strong>Звідки:</strong> {shipment.origin?.name || shipment.origin_name || '—'}
              </Typography>
              <Typography>
                <strong>Куди:</strong> {shipment.destination?.name || shipment.destination_name || '—'}
              </Typography>
              <Typography>
                <strong>Поточна локація:</strong> {shipment.current_location?.name || shipment.current_location_name || '—'}
              </Typography>
              <Typography>
                <strong>Тип оплати:</strong> {shipment.payment_type_display || shipment.payment_type || '—'}
              </Typography>
              <Typography>
                <strong>Статус оплати:</strong> {paymentLabel}
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

      <ConfirmDialog
        open={Boolean(confirmType)}
        onClose={() => setConfirmType(null)}
        onConfirm={handleConfirmAction}
        title="Підтвердження дії"
        message={
          confirmType === 'payment'
            ? 'Підтвердити оплату цієї посилки?'
            : confirmType === 'arrival'
              ? 'Підтвердити прибуття посилки до відділення призначення та перевести її у статус очікування видачі?'
              : confirmType === 'delivery'
                ? 'Підтвердити видачу посилки отримувачу?'
                : 'Скасувати цю посилку?'
        }
        confirmText={
          confirmType === 'payment'
            ? 'Підтвердити оплату'
            : confirmType === 'arrival'
              ? 'Підтвердити прибуття'
              : confirmType === 'delivery'
                ? 'Підтвердити видачу'
                : 'Скасувати посилку'
        }
        confirmColor={confirmType === 'cancel' ? 'error' : 'primary'}
        loading={
          confirmPaymentMutation.isPending ||
          markArrivalMutation.isPending ||
          confirmDeliveryMutation.isPending ||
          cancelMutation.isPending
        }
      />
    </>
  )
}
