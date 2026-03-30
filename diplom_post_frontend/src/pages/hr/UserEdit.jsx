import { useEffect, useState } from 'react'
import { Alert, Box, Stack, Typography } from '@mui/material'
import { useNavigate, useParams } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import LocationSelector from '../../components/domain/LocationSelector'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import { useUser, useUpdateUser } from '../../hooks/useUsers'
import { ROLE_LABELS, WORKER_ROLES } from '../../utils/constants'

export default function UserEdit() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: user, isLoading, isError, refetch } = useUser(id)
  const updateUserMutation = useUpdateUser()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [role, setRole] = useState('')
  const [location, setLocation] = useState(null)
  const [newPassword, setNewPassword] = useState('')
  const [formError, setFormError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    if (!user) return

    setUsername(user.username || '')
    setEmail(user.email || '')
    setFirstName(user.first_name || '')
    setLastName(user.last_name || '')
    setRole(user.role || '')
    setLocation(user.location || null)
  }, [user])

  if (isLoading) return <LoadingSpinner />
  if (isError || !user) return <ErrorState onRetry={refetch} />

  const roleOptions = WORKER_ROLES.map((value) => ({
    value,
    label: ROLE_LABELS[value] || value,
  }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    setSuccessMessage('')

    if (!username.trim()) {
      setFormError('Логін не може бути порожнім')
      return
    }

    const payload = {
      username,
      email,
      first_name: firstName,
      last_name: lastName,
      role,
      location: location?.id || null,
      ...(newPassword ? { password: newPassword } : {}),
    }

    try {
      await updateUserMutation.mutateAsync({ id: user.id, data: payload })
      setSuccessMessage('Дані працівника оновлено')
      refetch()
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося оновити працівника'
      setFormError(message)
    }
  }

  return (
    <>
      <PageHeader
        title={user.username || `Працівник #${user.id}`}
        subtitle="Редагування даних працівника"
        actions={
          <Button variant="text" onClick={() => navigate('/hr/users')}>
            Назад до списку
          </Button>
        }
      />

      <Card>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={3}>
            {formError && <Alert severity="error">{formError}</Alert>}
            {successMessage && <Alert severity="success">{successMessage}</Alert>}

            <Typography variant="h6" fontWeight={700}>
              Основні дані
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Логін"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Ім’я"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />
              <Input
                label="Прізвище"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Select
                label="Роль"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                options={roleOptions}
              />

              <LocationSelector
                value={location}
                onChange={setLocation}
                label="Локація"
                params={{}}
              />
            </Stack>

            <Typography variant="h6" fontWeight={700}>
              Зміна пароля
            </Typography>

            <Input
              label="Новий пароль"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              helperText="Залиш порожнім, якщо не потрібно змінювати пароль"
            />

            <Stack direction="row" spacing={2} justifyContent="flex-end">
              <Button
                variant="text"
                onClick={() => navigate('/hr/users')}
                disabled={updateUserMutation.isPending}
              >
                Скасувати
              </Button>

              <Button type="submit" disabled={updateUserMutation.isPending}>
                {updateUserMutation.isPending ? 'Збереження...' : 'Зберегти зміни'}
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Card>
    </>
  )
}