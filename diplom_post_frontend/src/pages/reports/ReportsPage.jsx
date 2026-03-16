import { useState } from 'react'
import { Box, Card, Grid, Typography, Button, TextField, Alert } from '@mui/material'
import { PictureAsPdfRounded, AssessmentRounded } from '@mui/icons-material'
import { downloadLocationReport } from '../../api/reports'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

export default function ReportsPage() {
  const { user } = useAuthStore()
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [loading, setLoading] = useState(false)

  const download = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (dateFrom) params.set('date_from', dateFrom)
      if (dateTo) params.set('date_to', dateTo)
      await downloadLocationReport(params.toString())
      toast.success('Звіт завантажено')
    } catch { toast.error('Помилка при завантаженні звіту') }
    finally { setLoading(false) }
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} color="primary.main" mb={1}>Звіти</Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Локація: {user?.location_name || '—'}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
              <AssessmentRounded color="primary" />
              <Typography variant="subtitle1" fontWeight={700}>Загальний звіт локації</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" mb={2.5}>
              Звіт містить всі посилки, Dispatch групи та статистику за обраний період.
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2.5 }}>
              <TextField label="Від" type="date" size="small" value={dateFrom}
                onChange={e => setDateFrom(e.target.value)} InputLabelProps={{ shrink: true }} />
              <TextField label="До" type="date" size="small" value={dateTo}
                onChange={e => setDateTo(e.target.value)} InputLabelProps={{ shrink: true }} />
            </Box>
            {!user?.location && (
              <Alert severity="warning" sx={{ mb: 2, borderRadius: 2 }}>
                Ви не прив'язані до жодної локації
              </Alert>
            )}
            <Button variant="contained" startIcon={<PictureAsPdfRounded />}
              onClick={download} disabled={loading || !user?.location}>
              {loading ? 'Завантаження...' : 'Завантажити PDF'}
            </Button>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ p: 3, bgcolor: '#F8FAFC' }}>
            <Typography variant="subtitle2" fontWeight={700} mb={1}>Звіти по посилках та групах</Typography>
            <Typography variant="body2" color="text.secondary">
              Звіти по конкретних посилках та Dispatch групах доступні на сторінках деталей:
            </Typography>
            <Box component="ul" sx={{ mt: 1.5, mb: 0, pl: 2.5 }}>
              {[
                'Квитанція прийому посилки',
                'Підтвердження доставки',
                'Звіт оплати',
                'Акт передачі Dispatch групи водію',
                'Акт прийому Dispatch групи',
              ].map(t => (
                <Typography key={t} component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>{t}</Typography>
              ))}
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
