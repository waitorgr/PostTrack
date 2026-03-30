import { useState } from 'react'
import { Alert, Box, Divider, Stack, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import {
  useRoute,
  useConfirmRoute,
  useStartRoute,
  useCompleteRoute,
  useGenerateDefaultRouteSteps,
} from '../../hooks/useRoutes'
import { fDateTime } from '../../utils/formatters'

export default function RouteDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: route, isLoading, isError, refetch } = useRoute(id)

  const confirmMutation = useConfirmRoute()
  const startMutation = useStartRoute()
  const completeMutation = useCompleteRoute()
  const generateStepsMutation = useGenerateDefaultRouteSteps()

  const [confirmType, setConfirmType] = useState(null)

  if (isLoading) return <LoadingSpinner />
  if (isError || !route) return <ErrorState onRetry={refetch} />

  const steps = route.steps || []
  const hasSteps = steps.length > 0

  const dispatchGroup = route.dispatch_group
    ? {
        id: route.dispatch_group,
        code: route.group_code || `Dispatch #${route.dispatch_group}`,
        status: route.dispatch_status,
      }
    : null

  const handleGenerateSteps = async () => {
    await generateStepsMutation.mutateAsync(route.id)
    refetch()
  }

  const handleConfirmAction = async () => {
    if (confirmType === 'confirm') {
      await confirmMutation.mutateAsync(route.id)
    }

    if (confirmType === 'start') {
      await startMutation.mutateAsync(route.id)
    }

    if (confirmType === 'complete') {
      await completeMutation.mutateAsync(route.id)
    }

    setConfirmType(null)
    refetch()
  }

  return (
    <>
      <PageHeader
        title={route.group_code ? `Маршрут ${route.group_code}` : `Маршрут #${route.id}`}
        subtitle="Перегляд деталей та керування маршрутом"
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Button variant="text" onClick={() => navigate('/logist/routes')}>
              Назад до списку
            </Button>

            {route.status === 'draft' && !hasSteps && (
              <Button
                color="secondary"
                onClick={handleGenerateSteps}
                disabled={generateStepsMutation.isPending}
              >
                {generateStepsMutation.isPending ? 'Генерація...' : 'Згенерувати кроки'}
              </Button>
            )}

            {route.status === 'draft' && (
              <Button
                onClick={() => setConfirmType('confirm')}
                disabled={!hasSteps}
              >
                Підтвердити
              </Button>
            )}

            {route.status === 'confirmed' && (
              <Button color="warning" onClick={() => setConfirmType('start')}>
                Почати виконання
              </Button>
            )}

            {route.status === 'in_progress' && (
              <Button color="success" onClick={() => setConfirmType('complete')}>
                Завершити маршрут
              </Button>
            )}
          </Stack>
        }
      />

      <Stack spacing={3}>
        {(confirmMutation.isError ||
          startMutation.isError ||
          completeMutation.isError ||
          generateStepsMutation.isError) && (
          <Alert severity="error">
            {generateStepsMutation.isError
              ? 'Не вдалося згенерувати кроки маршруту.'
              : 'Не вдалося виконати дію. Спробуй ще раз.'}
          </Alert>
        )}

        {route.status === 'draft' && !hasSteps && (
          <Alert severity="info">
            Щоб підтвердити маршрут, спочатку згенеруй кроки маршруту.
          </Alert>
        )}

        <Card>
          <Stack spacing={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
              <Typography variant="h6" fontWeight={700}>
                Загальна інформація
              </Typography>
              <StatusBadge status={route.status} type="route" />
            </Box>

            <Divider />

            <Stack spacing={1}>
              <Typography>
                <strong>Dispatch-група:</strong> {route.group_code || '—'}
              </Typography>
              <Typography>
                <strong>Створено:</strong> {fDateTime(route.created_at)}
              </Typography>
              <Typography>
                <strong>Запланований виїзд:</strong>{' '}
                {route.scheduled_departure ? fDateTime(route.scheduled_departure) : '—'}
              </Typography>
              <Typography>
                <strong>Початок:</strong> {route.origin_name || '—'}
              </Typography>
              <Typography>
                <strong>Кінець:</strong> {route.destination_name || '—'}
              </Typography>
              <Typography>
                <strong>Водій:</strong> {route.driver_name || '—'}
              </Typography>
              <Typography>
                <strong>Створив:</strong> {route.created_by_name || '—'}
              </Typography>
              <Typography>
                <strong>Кількість кроків:</strong> {route.step_count ?? steps.length ?? 0}
              </Typography>
              <Typography>
                <strong>Нотатки:</strong> {route.notes || '—'}
              </Typography>
            </Stack>
          </Stack>
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Кроки маршруту
          </Typography>

          {!steps.length ? (
            <Typography color="text.secondary">
              Для цього маршруту ще не додано кроків.
            </Typography>
          ) : (
            <Stack spacing={1.5}>
              {steps.map((step, index) => (
                <Box
                  key={step.id || index}
                  sx={{
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                  }}
                >
                  <Typography fontWeight={700}>
                    {step.order ?? index + 1}. {step.location_name || 'Локація'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Тип кроку: {step.step_type_display || step.step_type || '—'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Планове прибуття:{' '}
                    {step.planned_arrival ? fDateTime(step.planned_arrival) : '—'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Плановий виїзд:{' '}
                    {step.planned_departure ? fDateTime(step.planned_departure) : '—'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Фактичне прибуття:{' '}
                    {step.actual_arrival ? fDateTime(step.actual_arrival) : '—'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Фактичний виїзд:{' '}
                    {step.actual_departure ? fDateTime(step.actual_departure) : '—'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Нотатки: {step.notes || '—'}
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </Card>

        <Card>
          <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
            Пов’язана dispatch-група
          </Typography>

          {!dispatchGroup ? (
            <Typography color="text.secondary">
              До маршруту не прив’язано dispatch-групу.
            </Typography>
          ) : (
            <Box
              onClick={() => navigate(`/logist/dispatches/${dispatchGroup.id}`)}
              sx={{
                p: 2,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 2,
                cursor: 'pointer',
              }}
            >
              <Typography>
                {dispatchGroup.code || `Dispatch #${dispatchGroup.id}`}
              </Typography>

              {dispatchGroup.status ? (
                <StatusBadge status={dispatchGroup.status} type="dispatch" />
              ) : null}
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
          confirmType === 'confirm'
            ? 'Підтвердити цей маршрут?'
            : confirmType === 'start'
              ? 'Почати виконання цього маршруту?'
              : 'Завершити цей маршрут?'
        }
        confirmText={
          confirmType === 'confirm'
            ? 'Підтвердити'
            : confirmType === 'start'
              ? 'Почати'
              : 'Завершити'
        }
        loading={
          confirmMutation.isPending ||
          startMutation.isPending ||
          completeMutation.isPending
        }
      />
    </>
  )
}