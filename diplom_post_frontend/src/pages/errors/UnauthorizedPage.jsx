// src/pages/errors/UnauthorizedPage.jsx

import { Box, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'

export default function UnauthorizedPage() {
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
              403
            </Typography>
            <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>
              Недостатньо прав доступу
            </Typography>
            <Typography color="text.secondary">
              У тебе немає дозволу для перегляду цієї сторінки.
            </Typography>
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button onClick={() => navigate(-1)}>Назад</Button>
            <Button variant="outlined" onClick={() => navigate('/')}>
              На головну
            </Button>
          </Stack>
        </Stack>
      </Card>
    </Box>
  )
}