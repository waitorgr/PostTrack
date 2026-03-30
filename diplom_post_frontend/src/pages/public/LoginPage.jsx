import { useState } from 'react'
import { Alert, Box, Container, Stack, Typography } from '@mui/material'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import { useAuthStore } from '../../store/authStore'
import { useRoleRedirect } from '../../hooks/useRoleRedirect'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const getHomeRoute = useRoleRedirect()

  const login = useAuthStore((state) => state.login)
  const loading = useAuthStore((state) => state.loading)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState('')

  const successMessage = location.state?.message || ''

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')

    if (!username.trim() || !password.trim()) {
      setFormError('Заповни логін і пароль')
      return
    }

    const result = await login(username, password)

    if (!result.ok) {
      setFormError(result.error || 'Не вдалося увійти')
      return
    }

    const from = location.state?.from?.pathname
    const userRole = result.user?.role

    navigate(from || getHomeRoute(userRole), { replace: true })
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
                  Вхід у систему
                </Typography>
                <Typography color="text.secondary">
                  Увійди до свого кабінету відповідно до ролі.
                </Typography>
              </Box>

              {successMessage && <Alert severity="success">{successMessage}</Alert>}
              {formError && <Alert severity="error">{formError}</Alert>}

              <Input
                label="Логін"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />

              <Input
                label="Пароль"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />

              <Button type="submit" size="large" disabled={loading}>
                {loading ? 'Вхід...' : 'Увійти'}
              </Button>

              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Typography color="text.secondary">
                  Немає акаунта?
                </Typography>
                <Typography
                  component={RouterLink}
                  to="/register"
                  sx={{
                    textDecoration: 'none',
                    fontWeight: 700,
                    color: 'primary.main',
                  }}
                >
                  Зареєструватися
                </Typography>
              </Stack>

              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Typography color="text.secondary">
                  Потрібно лише відстеження?
                </Typography>
                <Typography
                  component={RouterLink}
                  to="/track"
                  sx={{
                    textDecoration: 'none',
                    fontWeight: 700,
                    color: 'primary.main',
                  }}
                >
                  Перейти до трекінгу
                </Typography>
              </Stack>
            </Stack>
          </Box>
        </Card>
      </Box>
    </Container>
  )
}