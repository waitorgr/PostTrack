import { useEffect, useState } from 'react'
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

  const trackingEvents = shipment?.tracking_events || shipment?.events || []

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
              placeholder="Наприклад: 0100100001"
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
          <Card>
            <Stack spacing={2}>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems={{ xs: 'flex-start', sm: 'center' }}
                flexDirection={{ xs: 'column', sm: 'row' }}
                gap={2}
              >
                <Box>
                  <Typography variant="h6" fontWeight={700}>
                    {shipment.tracking_number || '—'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Створено: {fDateTime(shipment.created_at)}
                  </Typography>
                </Box>

                <StatusBadge status={shipment.status} type="shipment" />
              </Box>

              <Box>
                <Typography>
                  <strong>Маршрут:</strong>{' '}
                  {shipment.origin?.name || shipment.origin_name || '—'} →{' '}
                  {shipment.destination?.name || shipment.destination_name || '—'}
                </Typography>
              </Box>
            </Stack>
          </Card>

          <Card>
            <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
              Історія руху
            </Typography>

            <TrackingTimeline events={trackingEvents} />
          </Card>
        </Stack>
      )}
    </>
  )
}