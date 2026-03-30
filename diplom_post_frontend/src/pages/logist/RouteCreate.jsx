import { useMemo, useState } from 'react'
import { Alert, Box, Stack, Typography } from '@mui/material'
import { useLocation, useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import LocationSelector from '../../components/domain/LocationSelector'
import UserSelector from '../../components/domain/UserSelector'
import DispatchGroupSelector from '../../components/domain/DispatchGroupSelector'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import { useCreateRoute } from '../../hooks/useRoutes'

export default function RouteCreate() {
  const navigate = useNavigate()
  const location = useLocation()

  const prefill = useMemo(() => location.state?.prefill || {}, [location.state])

  const [selectedDispatch, setSelectedDispatch] = useState(
    prefill.dispatchId
      ? {
          id: prefill.dispatchId,
          code: prefill.dispatchCode || `Dispatch #${prefill.dispatchId}`,
          origin_name: prefill.origin?.name || '',
          destination_name: prefill.destination?.name || '',
        }
      : null
  )

  const [name, setName] = useState(prefill.name || '')
  const [origin, setOrigin] = useState(prefill.origin || null)
  const [destination, setDestination] = useState(prefill.destination || null)
  const [driver, setDriver] = useState(prefill.driver || null)
  const [scheduledDeparture, setScheduledDeparture] = useState('')
  const [description, setDescription] = useState(prefill.description || '')
  const [formError, setFormError] = useState('')

  const createRouteMutation = useCreateRoute()

  const handleDispatchChange = (dispatch) => {
    setSelectedDispatch(dispatch)

    if (!dispatch) return

    if (!origin && dispatch.origin) {
      setOrigin({
        id: dispatch.origin,
        name: dispatch.origin_name || '',
      })
    }

    if (!destination && dispatch.destination) {
      setDestination({
        id: dispatch.destination,
        name: dispatch.destination_name || '',
      })
    }

    if (!name && dispatch.code) {
      setName(`Маршрут для ${dispatch.code}`)
    }
  }

  const handleSubmit = async (e) => {
  e.preventDefault()
  setFormError('')

  if (!selectedDispatch?.id) {
    setFormError('Оберіть dispatch-групу')
    return
  }

  if (!scheduledDeparture) {
    setFormError('Оберіть запланований час відправлення')
    return
  }

  const payload = {
    dispatch_group: selectedDispatch.id,
    scheduled_departure: scheduledDeparture,
    ...(driver?.id ? { driver: driver.id } : {}),
    ...(description ? { notes: description } : {}),
  }

  try {
    const created = await createRouteMutation.mutateAsync(payload)
    navigate(`/logist/routes/${created.id}`)
  } catch (error) {
    const message =
      error.response?.data?.detail ||
      Object.values(error.response?.data || {}).flat().join(' ') ||
      'Не вдалося створити маршрут'
    setFormError(message)
  }
}

  return (
    <>
      <PageHeader
        title="Створення маршруту"
        subtitle={
          prefill.dispatchId
            ? `Маршрут на основі dispatch-групи #${prefill.dispatchId}`
            : 'Оформлення нового маршруту для логістичного ланцюга'
        }
      />

      <Card>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={3}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <Typography variant="h6" fontWeight={700}>
              Основна інформація
            </Typography>

            <DispatchGroupSelector
              value={selectedDispatch}
              onChange={handleDispatchChange}
              label="Dispatch-група"
              params={{ status: 'ready' }}
              disabled={Boolean(prefill.dispatchId)}
            />

            <Input
              label="Запланований час відправлення"
              type="datetime-local"
              value={scheduledDeparture}
              onChange={(e) => setScheduledDeparture(e.target.value)}
              InputLabelProps={{ shrink: true }}
              required
            />

            <Input
              label="Назва маршруту"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Наприклад: Київ → Львів / ранковий рейс"
            />

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <LocationSelector
                value={origin}
                onChange={setOrigin}
                label="Початкова локація"
                params={{}}
              />

              <LocationSelector
                value={destination}
                onChange={setDestination}
                label="Кінцева локація"
                params={{}}
              />
            </Stack>

            <UserSelector
              value={driver}
              onChange={setDriver}
              label="Водій"
              params={{ role: 'driver' }}
            />

            <Input
              label="Опис"
              multiline
              minRows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Коментар до маршруту, особливості рейсу..."
            />

            <Stack direction="row" spacing={2} justifyContent="flex-end">
              <Button
                variant="text"
                onClick={() => navigate('/logist/routes')}
                disabled={createRouteMutation.isPending}
              >
                Скасувати
              </Button>

              <Button type="submit" disabled={createRouteMutation.isPending}>
                {createRouteMutation.isPending ? 'Створення...' : 'Створити маршрут'}
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Card>
    </>
  )
}