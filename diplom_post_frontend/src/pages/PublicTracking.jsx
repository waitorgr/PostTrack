import { useState } from 'react'
import { Box, Card, TextField, Button, Typography, CircularProgress,
  Alert, Stepper, Step, StepLabel, Chip, Divider } from '@mui/material'
import { SearchRounded, LocalShippingRounded, CheckCircleRounded } from '@mui/icons-material'
import { apiPublicTrack } from '../api/tracking'
import { fDateTime, STATUS_LABELS } from '../utils/formatters'
import { Link } from 'react-router-dom'

const STEPS = ['Прийнято', 'Відправлено', 'На сортуванні', 'В дорозі до вас', 'Доставлено']
const statusToStep = (s) => ({
  accepted: 0, picked_up_by_driver: 1, in_transit: 1,
  arrived_at_facility: 2, sorted: 2,
  out_for_delivery: 3, available_for_pickup: 3, delivered: 4,
}[s] ?? 0)

export default function PublicTracking() {
  const [num, setNum] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const search = async (e) => {
    e?.preventDefault()
    if (!num.trim()) return
    setError(''); setResult(null); setLoading(true)
    try {
      const data = await apiPublicTrack(num.trim().toUpperCase())
      setResult(data)
    } catch { setError('Посилку з таким номером не знайдено.') }
    finally { setLoading(false) }
  }

  const step = result ? statusToStep(result.status) : 0
  const isCancelled = ['cancelled','returned'].includes(result?.status)

  return (
    <Box sx={{
      minHeight: '100vh', background: 'linear-gradient(135deg, #0F172A 0%, #1B3F7A 60%, #1e3a8a 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', p: 3,
    }}>
      <Box sx={{ mb: 4, mt: 6, textAlign: 'center' }}>
        <Box sx={{
          width: 56, height: 56, borderRadius: '14px', mx: 'auto', mb: 2,
          background: 'rgba(255,255,255,.1)', backdropFilter: 'blur(10px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          border: '1px solid rgba(255,255,255,.15)',
        }}>
          <LocalShippingRounded sx={{ color: 'white', fontSize: 28 }} />
        </Box>
        <Typography variant="h4" fontWeight={800} color="white">Відстеження посилки</Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,.6)', mt: 0.5 }}>
          Введіть трекінг-номер у форматі UA123456789UA
        </Typography>
      </Box>

      <Card sx={{ width: '100%', maxWidth: 600, p: 3 }}>
        <Box component="form" onSubmit={search} sx={{ display: 'flex', gap: 1.5 }}>
          <TextField
            fullWidth placeholder="UA000000000UA" value={num}
            onChange={e => setNum(e.target.value.toUpperCase())}
            inputProps={{ style: { fontFamily: 'JetBrains Mono, monospace', fontWeight: 500, letterSpacing: '0.05em' } }}
          />
          <Button type="submit" variant="contained" disabled={loading} sx={{ px: 3, flexShrink: 0 }}>
            {loading ? <CircularProgress size={20} color="inherit" /> : <SearchRounded />}
          </Button>
        </Box>

        {error && <Alert severity="error" sx={{ mt: 2, borderRadius: 2 }}>{error}</Alert>}

        {result && (
          <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
              <Box>
                <Typography variant="overline" color="text.secondary">Трекінг-номер</Typography>
                <Typography fontFamily="JetBrains Mono, monospace" fontWeight={600} color="primary.main" fontSize="1.1rem">
                  {result.tracking_number}
                </Typography>
              </Box>
              <Chip
                label={STATUS_LABELS[result.status] || result.status_display}
                color={isCancelled ? 'error' : result.status === 'delivered' ? 'success' : 'info'}
                sx={{ fontWeight: 700 }}
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Box sx={{ flex: 1, p: 1.5, bgcolor: '#F8FAFC', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary">Відправник</Typography>
                <Typography variant="body2" fontWeight={600}>{result.sender_name}</Typography>
                <Typography variant="caption" color="text.secondary">{result.origin_city}</Typography>
              </Box>
              <Box sx={{ flex: 1, p: 1.5, bgcolor: '#F8FAFC', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary">Отримувач</Typography>
                <Typography variant="body2" fontWeight={600}>{result.receiver_name}</Typography>
                <Typography variant="caption" color="text.secondary">{result.destination_city}</Typography>
              </Box>
            </Box>

            {!isCancelled && (
              <Stepper activeStep={step} alternativeLabel sx={{ mb: 3 }}>
                {STEPS.map(l => <Step key={l}><StepLabel sx={{ '& .MuiStepLabel-label': { fontSize: '0.7rem' } }}>{l}</StepLabel></Step>)}
              </Stepper>
            )}

            {isCancelled && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                Посилку {result.status === 'returned' ? 'повернуто відправнику' : 'скасовано'}
              </Alert>
            )}

            <Divider sx={{ mb: 2 }} />
            <Typography variant="subtitle2" fontWeight={700} mb={1.5}>Історія подій</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {[...result.events].reverse().map((ev, i) => (
                <Box key={ev.id} sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  <Box sx={{
                    width: 8, height: 8, borderRadius: '50%', mt: 0.8, flexShrink: 0,
                    bgcolor: i === 0 ? 'primary.main' : '#CBD5E1',
                  }} />
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" fontWeight={600}>{ev.event_type_display}</Typography>
                      <Typography variant="caption" color="text.secondary">{fDateTime(ev.created_at)}</Typography>
                    </Box>
                    {ev.location_name && <Typography variant="caption" color="text.secondary">{ev.location_name}, {ev.location_city}</Typography>}
                    {ev.note && <Typography variant="caption" color="text.secondary" display="block">{ev.note}</Typography>}
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        )}
      </Card>

      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,.5)', mt: 3 }}>
        <Link to="/login" style={{ color: 'rgba(255,255,255,.7)', fontWeight: 600, textDecoration: 'none' }}>
          Увійти в систему
        </Link>
      </Typography>
    </Box>
  )
}
