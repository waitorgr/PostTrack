import { useMemo, useState } from 'react'
import { Alert, Box, Divider, LinearProgress, Stack, Typography } from '@mui/material'
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
  useStartRoute,
  useCompleteRoute,
  useMarkRouteStepArrival,
  useMarkRouteStepDeparture,
} from '../../hooks/useRoutes'
import { fDateTime } from '../../utils/formatters'

function getRouteSteps(route) {
  return route?.steps || []
}

function isStepArrivalDone(step) {
  return Boolean(step?.actual_arrival)
}

function isStepDepartureDone(step) {
  return Boolean(step?.actual_departure)
}

function isStepCompleted(step) {
  if (!step) return false

  if (step?.is_completed || step?.completed || step?.status === 'completed') {
    return true
  }

  if (step.step_type === 'destination') {
    return isStepArrivalDone(step)
  }

  return isStepDepartureDone(step)
}

function canMarkArrival(route, step) {
  if (!route || route.status !== 'in_progress' || !step) return false
  if (step.step_type === 'origin') return false
  if (step.actual_arrival) return false
  return true
}

function canMarkDeparture(route, step) {
  if (!route || route.status !== 'in_progress' || !step) return false
  if (step.step_type === 'destination') return false
  if (step.actual_departure) return false

  if (step.step_type === 'transit' && !step.actual_arrival) {
    return false
  }

  return true
}

function getNextStep(steps) {
  if (!steps.length) return null
  return steps.find((step) => !isStepCompleted(step)) || null
}

export default function RouteExecution() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: route, isLoading, isError, isFetching, refetch } = useRoute(id)

const startMutation = useStartRoute()
const completeMutation = useCompleteRoute()
const markArrivalMutation = useMarkRouteStepArrival()
const markDepartureMutation = useMarkRouteStepDeparture()

const isActionPending =
  startMutation.isPending ||
  completeMutation.isPending ||
  markArrivalMutation.isPending ||
  markDepartureMutation.isPending
  const [confirmType, setConfirmType] = useState(null)

  const steps = useMemo(() => getRouteSteps(route), [route])
  const nextStep = useMemo(() => getNextStep(steps), [steps])

  if (isLoading) return <LoadingSpinner minHeight={320} />
  if (isError || !route) return <ErrorState onRetry={refetch} />

  const completedCount = steps.filter(isStepCompleted).length
  const progressPercent = steps.length ? Math.round((completedCount / steps.length) * 100) : 0

  const dispatchGroup = route.dispatch_group
    ? {
        id: route.dispatch_group,
        code: route.group_code || `Dispatch #${route.dispatch_group}`,
        status: route.dispatch_status,
      }
    : null

      const handleMarkArrival = async (stepId) => {
  try {
    await markArrivalMutation.mutateAsync({
      routeId: route.id,
      data: { step_id: stepId },
    })
  } catch (error) {
    console.error(error)
  }
}

const handleMarkDeparture = async (stepId) => {
  try {
    await markDepartureMutation.mutateAsync({
      routeId: route.id,
      data: { step_id: stepId },
    })
  } catch (error) {
    console.error(error)
  }
}

  const handleConfirmAction = async () => {
  try {
    if (confirmType === 'start') {
      await startMutation.mutateAsync(route.id)
    } else if (confirmType === 'complete') {
      await completeMutation.mutateAsync(route.id)
    }

    setConfirmType(null)
  } catch (error) {
    console.error(error)
  }
}

  const mutationError =
  startMutation.isError ||
  completeMutation.isError ||
  markArrivalMutation.isError ||
  markDepartureMutation.isError

  return (
    <>
      <PageHeader
        title={route.group_code ? `Маршрут ${route.group_code}` : `Маршрут #${route.id}`}
        subtitle="Виконання маршруту"
      />

      {mutationError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Не вдалося виконати дію. Спробуй ще раз.
        </Alert>
      )}

      <Stack spacing={2.5}>
        <Card>
          <Stack spacing={2}>
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', md: 'row' },
                justifyContent: 'space-between',
                alignItems: { xs: 'flex-start', md: 'center' },
                gap: 2,
              }}
            >
              <Box>
                <Typography variant="h5" fontWeight={800}>
                  {route.group_code ? `Маршрут ${route.group_code}` : `Маршрут #${route.id}`}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  Створено: {fDateTime(route.created_at)}
                </Typography>
              </Box>

              <StatusBadge status={route.status} type="route" size="medium" />
            </Box>

            <Divider />

            <Stack spacing={1.25}>
              <Typography>
                <strong>Dispatch-група:</strong> {route.group_code || '—'}
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
                <strong>Нотатки:</strong> {route.notes || '—'}
              </Typography>
            </Stack>

            <Box sx={{ pt: 1 }}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1,
                  gap: 2,
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  Прогрес маршруту
                </Typography>
                <Typography variant="body2" fontWeight={700}>
                  {completedCount}/{steps.length || 0}
                </Typography>
              </Box>

              <LinearProgress
                variant="determinate"
                value={progressPercent}
                sx={{
                  height: 10,
                  borderRadius: 999,
                }}
              />

              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Виконано {progressPercent}%
              </Typography>
            </Box>
          </Stack>
        </Card>

        <Card>
          <Stack spacing={2}>
            <Typography variant="h6" fontWeight={800}>
              Наступна точка
            </Typography>

            {!nextStep ? (
              <Typography color="text.secondary">
                Для цього маршруту ще не визначено кроків.
              </Typography>
            ) : (
              <Box
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  border: '1px solid',
                  borderColor: 'divider',
                  backgroundColor: 'background.default',
                }}
              >
                <Typography variant="h6" fontWeight={700}>
                  {nextStep.location_name || 'Локація'}
                </Typography>

                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={2}
                  sx={{ mt: 1 }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Тип: {nextStep.step_type_display || nextStep.step_type || '—'}
                  </Typography>

                  <Typography variant="body2" color="text.secondary">
                    Порядок: {nextStep.order ?? '—'}
                  </Typography>
                </Stack>

                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Планове прибуття:{' '}
                  {nextStep.planned_arrival ? fDateTime(nextStep.planned_arrival) : '—'}
                </Typography>

                <Typography variant="body2" color="text.secondary">
                  Плановий виїзд:{' '}
                  {nextStep.planned_departure ? fDateTime(nextStep.planned_departure) : '—'}
                </Typography>
              </Box>
            )}
          </Stack>
        </Card>

        <Card>
          <Stack spacing={2}>
            <Typography variant="h6" fontWeight={800}>
              Дії маршруту
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              {route.status === 'confirmed' && (
  <Button
    size="large"
    sx={{ flex: 1, py: 1.5, fontSize: '1rem' }}
    onClick={() => setConfirmType('start')}
    disabled={isActionPending}
  >
    {startMutation.isPending ? 'Запуск...' : 'Почати маршрут'}
  </Button>
)}

{route.status === 'in_progress' && (
  <Button
    color="success"
    size="large"
    sx={{ flex: 1, py: 1.5, fontSize: '1rem' }}
    onClick={() => setConfirmType('complete')}
    disabled={isActionPending}
  >
    {completeMutation.isPending ? 'Завершення...' : 'Завершити маршрут'}
  </Button>
)}

<Button
  variant="outlined"
  size="large"
  sx={{ flex: 1, py: 1.5, fontSize: '1rem' }}
  onClick={() => refetch()}
  disabled={isLoading || isFetching || isActionPending}
>
  Оновити дані
</Button>
            </Stack>
          </Stack>
        </Card>

        <Card>
          <Stack spacing={2}>
            <Typography variant="h6" fontWeight={800}>
              Кроки маршруту
            </Typography>

            {!steps.length ? (
              <Typography color="text.secondary">
                Для цього маршруту ще не додано кроків.
              </Typography>
            ) : (
              <Stack spacing={1.5}>
                {steps.map((step, index) => {
                  const completed = isStepCompleted(step)
                  const isNext = nextStep?.id === step.id && !completed

                  return (
                    <Box
                      key={step.id || index}
                      sx={{
                        p: 2,
                        borderRadius: 3,
                        border: '1px solid',
                        borderColor: completed
                          ? 'success.main'
                          : isNext
                            ? 'primary.main'
                            : 'divider',
                        backgroundColor: completed
                          ? 'success.light'
                          : isNext
                            ? 'action.hover'
                            : 'background.paper',
                      }}
                    >
                      <Stack spacing={0.75}>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            gap: 2,
                            flexWrap: 'wrap',
                          }}
                        >
                          <Typography fontWeight={700}>
                            {step.order ?? index + 1}. {step.location_name || 'Локація'}
                          </Typography>

                          <Typography variant="body2" color="text.secondary">
                            {completed
                              ? 'Виконано'
                              : isNext
                                ? 'Наступна точка'
                                : 'Очікує'}
                          </Typography>
                        </Box>

                        <Typography variant="body2" color="text.secondary">
                          Тип: {step.step_type_display || step.step_type || '—'}
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
                          {route.status === 'in_progress' && (
  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25} sx={{ pt: 1 }}>
    {canMarkArrival(route, step) && (
      <Button
        variant="outlined"
        onClick={() => handleMarkArrival(step.id)}
        disabled={isActionPending}
      >
        {markArrivalMutation.isPending ? 'Фіксація...' : 'Зафіксувати прибуття'}
      </Button>
    )}

    {canMarkDeparture(route, step) && (
      <Button
        onClick={() => handleMarkDeparture(step.id)}
        disabled={isActionPending}
      >
        {markDepartureMutation.isPending ? 'Фіксація...' : 'Зафіксувати виїзд'}
      </Button>
    )}
  </Stack>
)}
                        </Typography>
                      </Stack>
                    </Box>
                  )
                })}
              </Stack>
            )}
          </Stack>
        </Card>

        <Card>
          <Stack spacing={1.5}>
            <Typography variant="h6" fontWeight={800}>
              Пов’язана dispatch-група
            </Typography>

            {!dispatchGroup ? (
              <Typography color="text.secondary">
                До цього маршруту не прив’язано dispatch-групу.
              </Typography>
            ) : (
              <Box
                onClick={() => navigate(`/driver/dispatches/${dispatchGroup.id}`)}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 2,
                  cursor: 'pointer',
                }}
              >
                <Typography fontWeight={600}>
                  {dispatchGroup.code || `Dispatch #${dispatchGroup.id}`}
                </Typography>

                {dispatchGroup.status ? (
                  <StatusBadge status={dispatchGroup.status} type="dispatch" />
                ) : null}
              </Box>
            )}
          </Stack>
        </Card>
      </Stack>

      <ConfirmDialog
        open={Boolean(confirmType)}
        onClose={() => setConfirmType(null)}
        onConfirm={handleConfirmAction}
        title="Підтвердження дії"
        message={
          confirmType === 'start'
            ? 'Почати виконання цього маршруту?'
            : 'Завершити цей маршрут?'
        }
        confirmText={confirmType === 'start' ? 'Почати маршрут' : 'Завершити маршрут'}
        confirmColor={confirmType === 'complete' ? 'success' : 'primary'}
        loading={isActionPending}
      />
    </>
  )
}