import { useEffect, useMemo, useState } from 'react'
import { Alert, Box, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import PageHeader from '../../components/common/PageHeader'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import TrackingTimeline from '../../components/domain/TrackingTimeline'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import { fDateTime } from '../../utils/formatters'

async function apiTrackShipment(trackingCode) {
  const response = await client.get(`/shipments/track/${trackingCode}/`)
  return response.data
}

function buildPublicTrackingEvents(shipment) {
  const rawEvents = shipment?.tracking_events || shipment?.events || []

  const visibleStatuses = new Set([
    'accepted',
    'arrived_at_facility',
    'available_for_pickup',
    'delivered',
  ])

  const normalizeText = (value) =>
    String(value || '')
      .replace(/\s+/g, ' ')
      .trim()

  const removeTrailingDot = (value) =>
    normalizeText(value).replace(/\.\s*$/, '')

  const buildTitleFromNote = (event) => {
    const status = event.status || event.event_type
    const note = normalizeText(event.note)
    const locationName = event.location?.name || event.location_name || ''

    if (status === 'accepted') {
      if (locationName) {
        return `Прийнято у відділенні ${locationName}`
      }
      return note ? removeTrailingDot(note) : 'Прийнято'
    }

    if (status === 'arrived_at_facility') {
      if (note) {
        return removeTrailingDot(
          note
            .replace(/^Посилка прибула до\s+/i, 'Прибуло до ')
            .replace(/^Відправлення прибула до\s+/i, 'Прибуло до ')
            .replace(/^Відправлення прибуло до\s+/i, 'Прибуло до ')
        )
      }
      return 'Прибуло до обʼєкта'
    }

    if (status === 'available_for_pickup') {
      return 'Очікує отримання'
    }

    if (status === 'delivered') {
      return 'Доставлено'
    }

    return removeTrailingDot(note) || event.event_type_label || 'Подія'
  }

  return rawEvents
    .filter((event) => visibleStatuses.has(event.status || event.event_type))
    .map((event, index) => {
      const status = event.status || event.event_type

      return {
        id: event.id || `${status}-${event.created_at || index}`,
        title: buildTitleFromNote(event),
        created_at: event.created_at,
        status,
        note: event.note || '',
      }
    })
    .sort((a, b) => {
      const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
      const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
      return timeA - timeB
    })
}

export default function PublicTrackingPage() {
  const navigate = useNavigate()
  const { trackingCode } = useParams()

  const [inputValue, setInputValue] = useState(trackingCode || '')

  useEffect(() => {
    setInputValue(trackingCode || '')
  }, [trackingCode])

  const {
    data: shipment,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['public-tracking', trackingCode],
    queryFn: () => apiTrackShipment(trackingCode),
    enabled: Boolean(trackingCode),
    retry: 0,
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    const normalized = inputValue.trim()
    if (!normalized) return

    navigate(`/track/${normalized}`)
  }

  const publicTrackingEvents = useMemo(
    () => buildPublicTrackingEvents(shipment),
    [shipment]
  )

  return (
    <>
      <PageHeader
        title="Відстеження посилки"
        subtitle="Введи трек-номер, щоб перевірити поточний стан відправлення"
      />

      <Card sx={{ mb: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            alignItems={{ xs: 'stretch', md: 'center' }}
          >
            <Input
              label="Трек-номер"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Наприклад: UA123456789UA"
            />

            <Button type="submit" sx={{ minWidth: { md: 180 } }}>
              Знайти
            </Button>
          </Stack>
        </Box>
      </Card>

      {!trackingCode ? null : isLoading ? (
        <LoadingSpinner />
      ) : isError ? (
        error?.response?.status === 404 ? (
          <Alert severity="warning">
            Посилку з таким трек-номером не знайдено.
          </Alert>
        ) : (
          <ErrorState onRetry={refetch} />
        )
      ) : !shipment ? (
        <Alert severity="warning">
          Не вдалося отримати дані по відправленню.
        </Alert>
      ) : (
        <Stack spacing={3}>
          <Card
            sx={{
              borderRadius: 4,
              bgcolor: '#f7f7f7',
            }}
          >
            <Stack spacing={1.5}>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems={{ xs: 'flex-start', sm: 'center' }}
                flexDirection={{ xs: 'column', sm: 'row' }}
                gap={2}
              >
                <Box>
                  <Typography variant="h5" fontWeight={800}>
                    {shipment.tracking_number || '—'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Створено: {fDateTime(shipment.created_at)}
                  </Typography>
                </Box>

                <StatusBadge status={shipment.status} type="shipment" />
              </Box>

              <Typography>
                <strong>Маршрут:</strong>{' '}
                {shipment.origin?.name || shipment.origin_name || '—'} →{' '}
                {shipment.destination?.name || shipment.destination_name || '—'}
              </Typography>

              <Typography>
                <strong>Поточне місце:</strong>{' '}
                {shipment.current_location?.name || shipment.current_location_name || '—'}
              </Typography>
            </Stack>
          </Card>

          <Card>
            <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
              Трекінг
            </Typography>

            <TrackingTimeline events={publicTrackingEvents} variant="public" />
          </Card>
        </Stack>
      )}
    </>
  )
}