// src/pages/errors/NotFoundPage.jsx

import { Box, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        minHeight: '70vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 560 }}>
        <Stack spacing={3} alignItems="flex-start">
          <Box>
            <Typography variant="h3" fontWeight={800} sx={{ mb: 1 }}>
              404
            </Typography>
            <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>
              Сторінку не знайдено
            </Typography>
            <Typography color="text.secondary">
              Можливо, адреса введена неправильно або сторінка була переміщена.
            </Typography>
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button onClick={() => navigate('/')}>На головну</Button>
            <Button variant="outlined" onClick={() => navigate(-1)}>
              Назад
            </Button>
          </Stack>
        </Stack>
      </Card>
    </Box>
  )
}