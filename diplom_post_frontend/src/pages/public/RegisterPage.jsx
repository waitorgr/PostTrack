import { useState } from 'react'
import { Alert, Box, Container, Stack, Typography } from '@mui/material'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import { apiRegisterCustomer } from '../../api/auth'

export default function RegisterPage() {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [formError, setFormError] = useState('')

  const registerMutation = useMutation({
    mutationFn: apiRegisterCustomer,
    onSuccess: () => {
      navigate('/login', {
        replace: true,
        state: {
          message: 'Реєстрація успішна. Тепер увійди в систему.',
        },
      })
    },
    onError: (error) => {
      const message =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося зареєструватися'
      setFormError(message)
    },
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')

    if (!username.trim()) {
      setFormError('Вкажи логін')
      return
    }

    if (!email.trim()) {
      setFormError('Вкажи email')
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
      password,
      role: 'customer',
    }

    registerMutation.mutate(payload)
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          display: 'flex',
          alignItems: 'center',
          py: 6,
        }}
      >
        <Card sx={{ width: '100%' }}>
          <Box component="form" onSubmit={handleSubmit}>
            <Stack spacing={3}>
              <Box>
                <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
                  Реєстрація
                </Typography>
                <Typography color="text.secondary">
                  Створи клієнтський акаунт для перегляду та відстеження своїх посилок.
                </Typography>
              </Box>

              {formError && <Alert severity="error">{formError}</Alert>}

              <Input
                label="Логін"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />

              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />

              <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                <Input
                  label="Ім’я"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  autoComplete="given-name"
                />

                <Input
                  label="Прізвище"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  autoComplete="family-name"
                />
              </Stack>

              <Input
                label="Пароль"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />

              <Input
                label="Підтвердження пароля"
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                autoComplete="new-password"
              />

              <Button type="submit" size="large" disabled={registerMutation.isPending}>
                {registerMutation.isPending ? 'Реєстрація...' : 'Зареєструватися'}
              </Button>

              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Typography color="text.secondary">
                  Уже є акаунт?
                </Typography>
                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    textDecoration: 'none',
                    fontWeight: 700,
                    color: 'primary.main',
                  }}
                >
                  Увійти
                </Typography>
              </Stack>
            </Stack>
          </Box>
        </Card>
      </Box>
    </Container>
  )
}