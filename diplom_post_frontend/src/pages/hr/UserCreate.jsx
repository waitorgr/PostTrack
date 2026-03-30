import { useState } from 'react'
import { Alert, Box, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import LocationSelector from '../../components/domain/LocationSelector'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import { useCreateUser } from '../../hooks/useUsers'
import { ROLE_LABELS, WORKER_ROLES } from '../../utils/constants'

export default function UserCreate() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [role, setRole] = useState('postal_worker')
  const [location, setLocation] = useState(null)
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [formError, setFormError] = useState('')

  const createUserMutation = useCreateUser()

  const roleOptions = WORKER_ROLES.map((value) => ({
    value,
    label: ROLE_LABELS[value] || value,
  }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')

    if (!username.trim()) {
      setFormError('Вкажи логін користувача')
      return
    }

    if (!role) {
      setFormError('Оберіть роль')
      return
    }

    if (!password || password.length < 6) {
      setFormError('Пароль має містити щонайменше 6 символів')
      return
    }

    if (password !== passwordConfirm) {
      setFormError('Паролі не співпадають')
      return
    }

    const payload = {
      username,
      email,
      first_name: firstName,
      last_name: lastName,
      role,
      password,
      ...(location?.id ? { location: location.id } : {}),
    }

    try {
      const created = await createUserMutation.mutateAsync(payload)
      navigate(`/hr/users/${created.id}/edit`)
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося створити працівника'
      setFormError(message)
    }
  }

  return (
    <>
      <PageHeader
        title="Створення працівника"
        subtitle="Додавання нового користувача внутрішньої системи"
      />

      <Card>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={3}>
            {formError && <Alert severity="error">{formError}</Alert>}

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
              Дані для входу
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Пароль"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <Input
                label="Підтвердження пароля"
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
              />
            </Stack>

            <Stack direction="row" spacing={2} justifyContent="flex-end">
              <Button
                variant="text"
                onClick={() => navigate('/hr/users')}
                disabled={createUserMutation.isPending}
              >
                Скасувати
              </Button>

              <Button type="submit" disabled={createUserMutation.isPending}>
                {createUserMutation.isPending ? 'Створення...' : 'Створити працівника'}
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Card>
    </>
  )
}