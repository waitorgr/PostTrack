import { Box, Container, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <Container maxWidth="lg">
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          display: 'flex',
          alignItems: 'center',
          py: 6,
        }}
      >
        <Stack spacing={5} sx={{ width: '100%' }}>
          <Box sx={{ maxWidth: 760 }}>
            <Typography
              variant="h2"
              fontWeight={800}
              sx={{
                fontSize: { xs: '2rem', md: '3.25rem' },
                lineHeight: 1.1,
                mb: 2,
              }}
            >
              Система управління внутрішніми поштовими відправленнями
            </Typography>

            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ maxWidth: 700, mb: 4, fontWeight: 400 }}
            >
              Веб-орієнтована система для створення, маршрутизації, сортування,
              перевезення та відстеження посилок між внутрішніми поштовими вузлами.
            </Typography>

            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={2}
              sx={{ maxWidth: 420 }}
            >
              <Button size="large" onClick={() => navigate('/login')}>
                Увійти
              </Button>

              <Button
                size="large"
                variant="outlined"
                onClick={() => navigate('/register')}
              >
                Реєстрація
              </Button>

              <Button
                size="large"
                variant="text"
                onClick={() => navigate('/track')}
              >
                Відстежити
              </Button>
            </Stack>
          </Box>

          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: {
                xs: '1fr',
                md: 'repeat(3, 1fr)',
              },
            }}
          >
            <Card>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 1.5 }}>
                Повний цикл доставки
              </Typography>
              <Typography color="text.secondary">
                Від створення посилки у відділенні до її видачі отримувачу.
              </Typography>
            </Card>

            <Card>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 1.5 }}>
                Рольові кабінети
              </Typography>
              <Typography color="text.secondary">
                Окремі інтерфейси для працівника відділення, складу, логіста,
                водія, HR, клієнта та адміністратора.
              </Typography>
            </Card>

            <Card>
              <Typography variant="h6" fontWeight={700} sx={{ mb: 1.5 }}>
                Прозорий трекінг
              </Typography>
              <Typography color="text.secondary">
                Відстеження статусів і подій руху посилки у внутрішній системі.
              </Typography>
            </Card>
          </Box>
        </Stack>
      </Box>
    </Container>
  )
}