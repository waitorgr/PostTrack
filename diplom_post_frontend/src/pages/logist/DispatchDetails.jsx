import { Box, Divider, Stack, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import ShipmentTable from '../../components/domain/ShipmentTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import { apiGetDispatchGroup } from '../../api/dispatch'
import { fDateTime } from '../../utils/formatters'

export default function DispatchDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: dispatchGroup, isLoading, isError, refetch } = useQuery({
    queryKey: ['logist', 'dispatch-group', id],
    queryFn: () => apiGetDispatchGroup(id),
    enabled: Boolean(id),
  })

  if (isLoading) return <LoadingSpinner />
  if (isError || !dispatchGroup) return <ErrorState onRetry={refetch} />

  const shipments = dispatchGroup.shipments?.length
    ? dispatchGroup.shipments
    : (dispatchGroup.items || []).map((item) => ({
        ...(item.shipment_detail || {}),
        dispatch_item_id: item.id,
        tracking_number:
          item.shipment_tracking_number ||
          item.shipment_detail?.tracking_number ||
          '',
        shipment_id: item.shipment,
      }))

  const routePrefill = {
    dispatchId: dispatchGroup.id,
    name: dispatchGroup.code
      ? `Маршрут для ${dispatchGroup.code}`
      : `Маршрут для dispatch #${dispatchGroup.id}`,
    origin: dispatchGroup.origin
      ? {
          id: dispatchGroup.origin,
          name: dispatchGroup.origin_name || 'Початкова локація',
        }
      : null,
    destination: dispatchGroup.destination
      ? {
          id: dispatchGroup.destination,
          name: dispatchGroup.destination_name || 'Кінцева локація',
        }
      : null,
    driver: dispatchGroup.driver
      ? {
          id: dispatchGroup.driver,
          username: dispatchGroup.driver_name || 'Водій',
        }
      : null,
    description: dispatchGroup.code
      ? `Маршрут створено на основі dispatch-групи ${dispatchGroup.code}.`
      : `Маршрут створено на основі dispatch-групи #${dispatchGroup.id}.`,
  }

  return (
    <>
      <PageHeader
        title={dispatchGroup.code || dispatchGroup.name || `Dispatch #${dispatchGroup.id}`}
        subtitle="Деталі dispatch-групи для логіста"
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Button variant="text" onClick={() => navigate('/logist/dispatches')}>
              Назад до списку
            </Button>

            <Button
  onClick={() =>
    navigate('/logist/routes/create', {
      state: {
        prefill: {
          dispatchId: dispatchGroup.id,
          dispatchCode: dispatchGroup.code,
          name: dispatchGroup.code
            ? `Маршрут для ${dispatchGroup.code}`
            : `Маршрут для dispatch #${dispatchGroup.id}`,
          origin: dispatchGroup.origin
            ? {
                id: dispatchGroup.origin,
                name: dispatchGroup.origin_name || 'Початкова локація',
              }
            : null,
          destination: dispatchGroup.destination
            ? {
                id: dispatchGroup.destination,
                name: dispatchGroup.destination_name || 'Кінцева локація',
              }
            : null,
          driver: dispatchGroup.driver
            ? {
                id: dispatchGroup.driver,
                username: dispatchGroup.driver_name || 'Водій',
              }
            : null,
          description: dispatchGroup.code
            ? `Маршрут створено на основі dispatch-групи ${dispatchGroup.code}.`
            : `Маршрут створено на основі dispatch-групи #${dispatchGroup.id}.`,
        },
      },
    })
  }
>
  Створити маршрут
</Button>
          </Stack>
        }
      />

      <Stack spacing={3}>
        <Card>
          <Stack spacing={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
              <Typography variant="h6" fontWeight={700}>
                Інформація про групу
              </Typography>
              <StatusBadge status={dispatchGroup.status} type="dispatch" />
            </Box>

            <Divider />

            <Typography>
              <strong>Код:</strong> {dispatchGroup.code || '—'}
            </Typography>
            <Typography>
              <strong>Створено:</strong> {fDateTime(dispatchGroup.created_at)}
            </Typography>
            <Typography>
              <strong>Статус:</strong> {dispatchGroup.status_display || dispatchGroup.status || '—'}
            </Typography>
            <Typography>
              <strong>Походження:</strong> {dispatchGroup.origin_name || '—'}
            </Typography>
            <Typography>
              <strong>Призначення:</strong> {dispatchGroup.destination_name || '—'}
            </Typography>
            <Typography>
              <strong>Поточна локація:</strong> {dispatchGroup.current_location_name || '—'}
            </Typography>
            <Typography>
              <strong>Водій:</strong> {dispatchGroup.driver_name || '—'}
            </Typography>
            <Typography>
              <strong>Кількість посилок:</strong>{' '}
              {dispatchGroup.shipment_count ?? shipments.length ?? 0}
            </Typography>
          </Stack>
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Посилки в групі
          </Typography>

          <ShipmentTable
            rows={shipments}
            loading={false}
            onRowClick={undefined}
          />
        </Card>
      </Stack>
    </>
  )
}