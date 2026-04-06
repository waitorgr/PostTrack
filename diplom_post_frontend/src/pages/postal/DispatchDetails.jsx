import { useState } from 'react'
import { Alert, Box, Divider, Stack, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import ShipmentTable from '../../components/domain/ShipmentTable'
import StatusBadge from '../../components/domain/StatusBadge'
import {
  apiAddShipmentToDispatch,
  apiArriveDispatch,
  apiDeleteDispatchGroup,
  apiDepartDispatch,
  apiGetDispatchGroup,
  apiMarkDispatchReady,
  apiRemoveShipmentFromDispatch,
} from '../../api/dispatch'
import { fDateTime } from '../../utils/formatters'

export default function DispatchDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [trackingNumber, setTrackingNumber] = useState('')
  const [confirmType, setConfirmType] = useState(null)
  const [message, setMessage] = useState('')

  const { data: dispatchGroup, isLoading, isError, refetch } = useQuery({
    queryKey: ['dispatch-group', id],
    queryFn: () => apiGetDispatchGroup(id),
    enabled: Boolean(id),
  })

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['dispatch-group', id] })
    await queryClient.invalidateQueries({ queryKey: ['dispatch-groups'] })
  }

  const addShipmentMutation = useMutation({
    mutationFn: ({ dispatchId, tracking }) => apiAddShipmentToDispatch(dispatchId, tracking),
    onSuccess: async () => {
      setTrackingNumber('')
      setMessage('Посилку додано до групи')
      await invalidate()
      refetch()
    },
    onError: (error) => {
      setMessage(
        error.response?.data?.detail ||
          Object.values(error.response?.data || {}).flat().join(' ') ||
          'Не вдалося додати посилку'
      )
    },
  })

  const removeShipmentMutation = useMutation({
    mutationFn: ({ dispatchId, tracking }) => apiRemoveShipmentFromDispatch(dispatchId, tracking),
    onSuccess: async () => {
      setMessage('Посилку видалено з групи')
      await invalidate()
      refetch()
    },
    onError: (error) => {
      setMessage(
        error.response?.data?.detail ||
          Object.values(error.response?.data || {}).flat().join(' ') ||
          'Не вдалося видалити посилку'
      )
    },
  })

  const markReadyMutation = useMutation({
    mutationFn: apiMarkDispatchReady,
    onSuccess: async () => {
      setMessage('Групу позначено як готову')
      await invalidate()
      refetch()
    },
    onError: (error) => {
      setMessage(
        error.response?.data?.detail ||
          Object.values(error.response?.data || {}).flat().join(' ') ||
          'Не вдалося змінити статус групи'
      )
    },
  })

  const departMutation = useMutation({
    mutationFn: apiDepartDispatch,
    onSuccess: async () => {
      setMessage('Групу відправлено. PDF-звіт завантажено.')
      await invalidate()
      refetch()
    },
    onError: (error) => {
      setMessage(
        error.response?.data?.detail ||
          Object.values(error.response?.data || {}).flat().join(' ') ||
          'Не вдалося відправити групу'
      )
    },
  })

  const arriveMutation = useMutation({
    mutationFn: apiArriveDispatch,
    onSuccess: async () => {
      setMessage('Прибуття групи підтверджено. PDF-звіт завантажено.')
      await invalidate()
      refetch()
    },
    onError: (error) => {
      setMessage(
        error.response?.data?.detail ||
          Object.values(error.response?.data || {}).flat().join(' ') ||
          'Не вдалося підтвердити прибуття групи'
      )
    },
  })

  const deleteDispatchMutation = useMutation({
    mutationFn: apiDeleteDispatchGroup,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['dispatch-groups'] })
      navigate('/postal/dispatch')
    },
    onError: (error) => {
      setMessage(
        error.response?.data?.detail ||
          Object.values(error.response?.data || {}).flat().join(' ') ||
          'Не вдалося видалити dispatch-групу'
      )
    },
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

  const handleAddShipment = async () => {
    if (!trackingNumber.trim()) return
    setMessage('')
    await addShipmentMutation.mutateAsync({
      dispatchId: dispatchGroup.id,
      tracking: trackingNumber.trim(),
    })
  }

  const handleConfirmAction = async () => {
    if (confirmType === 'ready') {
      await markReadyMutation.mutateAsync(dispatchGroup.id)
    }

    if (confirmType === 'depart') {
      await departMutation.mutateAsync(dispatchGroup.id)
    }

    if (confirmType === 'arrive') {
      await arriveMutation.mutateAsync(dispatchGroup.id)
    }

    if (confirmType === 'delete') {
      await deleteDispatchMutation.mutateAsync(dispatchGroup.id)
    }

    setConfirmType(null)
  }

  return (
    <>
      <PageHeader
        title={dispatchGroup.code || dispatchGroup.name || `Dispatch #${dispatchGroup.id}`}
        subtitle="Деталі dispatch-групи та керування її складом"
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {dispatchGroup.status === 'forming' && (
              <>
                <Button color="warning" onClick={() => setConfirmType('ready')}>
                  Позначити готовою
                </Button>

                <Button color="error" onClick={() => setConfirmType('delete')}>
                  Видалити групу
                </Button>
              </>
            )}

            {dispatchGroup.status === 'ready' && (
              <Button color="primary" onClick={() => setConfirmType('depart')}>
                Відправити
              </Button>
            )}

            {dispatchGroup.status === 'in_transit' && (
              <Button color="success" onClick={() => setConfirmType('arrive')}>
                Підтвердити прибуття
              </Button>
            )}
          </Stack>
        }
      />

      <Stack spacing={3}>
        {message && <Alert severity="info">{message}</Alert>}

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
              <strong>Кількість посилок:</strong> {dispatchGroup.shipment_count ?? shipments.length ?? 0}
            </Typography>
          </Stack>
        </Card>

        {dispatchGroup.status === 'forming' && (
          <Card>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>
                Додати посилку до групи
              </Typography>

              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <Input
                  label="Трек-номер"
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  placeholder="Введи трек-номер"
                />
                <Button
                  onClick={handleAddShipment}
                  disabled={addShipmentMutation.isPending}
                >
                  Додати
                </Button>
              </Stack>
            </Stack>
          </Card>
        )}

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Посилки в групі
          </Typography>

          <ShipmentTable
            rows={shipments}
            loading={false}
            onRowClick={undefined}
          />

          {dispatchGroup.status === 'forming' && shipments.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Щоб прибрати посилку з групи, натисни кнопку нижче для вибраного трек-номера.
              </Typography>

              <Stack spacing={1}>
                {shipments.map((shipment) => (
                  <Button
                    key={shipment.id || shipment.tracking_number}
                    variant="text"
                    color="error"
                    onClick={() =>
                      removeShipmentMutation.mutate({
                        dispatchId: dispatchGroup.id,
                        tracking: shipment.tracking_number,
                      })
                    }
                  >
                    Видалити {shipment.tracking_number}
                  </Button>
                ))}
              </Stack>
            </Box>
          )}
        </Card>
      </Stack>

      <ConfirmDialog
        open={Boolean(confirmType)}
        onClose={() => setConfirmType(null)}
        onConfirm={handleConfirmAction}
        title="Підтвердження дії"
        message={
          confirmType === 'ready'
            ? 'Позначити групу як готову до відправлення?'
            : confirmType === 'depart'
              ? 'Підтвердити відправлення цієї групи?'
              : confirmType === 'delete'
                ? 'Видалити цю dispatch-групу? Цю дію не можна скасувати.'
                : 'Підтвердити прибуття цієї групи?'
        }
        confirmText={
          confirmType === 'ready'
            ? 'Позначити готовою'
            : confirmType === 'depart'
              ? 'Відправити'
              : confirmType === 'delete'
                ? 'Видалити'
                : 'Підтвердити прибуття'
        }
        loading={
          markReadyMutation.isPending ||
          departMutation.isPending ||
          arriveMutation.isPending ||
          deleteDispatchMutation.isPending
        }
      />
    </>
  )
}