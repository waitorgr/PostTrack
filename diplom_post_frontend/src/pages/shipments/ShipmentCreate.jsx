import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Card, Grid, TextField, Button, Typography, MenuItem,
  Divider, Alert, CircularProgress, InputAdornment } from '@mui/material'
import { ArrowBackRounded, SaveRounded } from '@mui/icons-material'
import { apiCreateShipment } from '../../api/shipments'
import { apiGetLocations } from '../../api/locations'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

const FIELD = (label, key, form, set, opts = {}) => (
  <TextField
    label={label} fullWidth required={opts.required !== false}
    value={form[key] || ''} onChange={e => set(p => ({ ...p, [key]: e.target.value }))}
    {...opts}
  />
)

export default function ShipmentCreate() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    sender_first_name: '', sender_last_name: '', sender_patronymic: '',
    sender_phone: '', sender_email: '',
    receiver_first_name: '', receiver_last_name: '', receiver_patronymic: '',
    receiver_phone: '', receiver_email: '',
    destination: '', weight: '', description: '', payment_type: 'prepaid',
  })

  useEffect(() => {
    apiGetLocations({ type: 'post_office' }).then(r => setLocations(r.results || r))
  }, [])

  const price = form.weight ? (30 + 15 * parseFloat(form.weight || 0)).toFixed(2) : null

  const handle = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const sh = await apiCreateShipment({ ...form, weight: parseFloat(form.weight) })
      toast.success('Посилку створено!')
      navigate(`/shipments/${sh.id}`)
    } catch (err) {
      const d = err.response?.data
      setError(d ? Object.entries(d).map(([k,v]) => `${k}: ${v}`).join('; ') : 'Помилка')
    } finally { setLoading(false) }
  }

  const s = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }))

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBackRounded />} onClick={() => navigate('/shipments')}>Назад</Button>
        <Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">Нова посилка</Typography>
          <Typography variant="body2" color="text.secondary">Відділення: {user?.location_name}</Typography>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}

      <Box component="form" onSubmit={handle}>
        <Grid container spacing={3}>
          {/* Відправник */}
          <Grid item xs={12} md={6}>
            <Card sx={{ p: 2.5 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2} color="primary.main">Відправник</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}><TextField label="Прізвище" fullWidth required value={form.sender_last_name} onChange={s('sender_last_name')} /></Grid>
                <Grid item xs={6}><TextField label="Ім'я" fullWidth required value={form.sender_first_name} onChange={s('sender_first_name')} /></Grid>
                <Grid item xs={12}><TextField label="По-батькові" fullWidth required value={form.sender_patronymic} onChange={s('sender_patronymic')} /></Grid>
                <Grid item xs={12}><TextField label="Телефон" fullWidth required value={form.sender_phone} onChange={s('sender_phone')} placeholder="+380XXXXXXXXX" /></Grid>
                <Grid item xs={12}><TextField label="Email" fullWidth value={form.sender_email} onChange={s('sender_email')} type="email" /></Grid>
                <Grid item xs={12}>
                  <TextField label="Відділення відправлення" fullWidth disabled value={user?.location_name || '—'}
                    helperText="Визначається автоматично" />
                </Grid>
              </Grid>
            </Card>
          </Grid>

          {/* Отримувач */}
          <Grid item xs={12} md={6}>
            <Card sx={{ p: 2.5 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2} color="primary.main">Отримувач</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}><TextField label="Прізвище" fullWidth required value={form.receiver_last_name} onChange={s('receiver_last_name')} /></Grid>
                <Grid item xs={6}><TextField label="Ім'я" fullWidth required value={form.receiver_first_name} onChange={s('receiver_first_name')} /></Grid>
                <Grid item xs={12}><TextField label="По-батькові" fullWidth required value={form.receiver_patronymic} onChange={s('receiver_patronymic')} /></Grid>
                <Grid item xs={12}><TextField label="Телефон" fullWidth required value={form.receiver_phone} onChange={s('receiver_phone')} placeholder="+380XXXXXXXXX" /></Grid>
                <Grid item xs={12}><TextField label="Email" fullWidth value={form.receiver_email} onChange={s('receiver_email')} type="email" /></Grid>
                <Grid item xs={12}>
                  <TextField select label="Відділення призначення" fullWidth required value={form.destination} onChange={s('destination')}>
                    <MenuItem value="">Оберіть відділення</MenuItem>
                    {locations.filter(l => l.id !== user?.location).map(l => (
                      <MenuItem key={l.id} value={l.id}>{l.name} — {l.city}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>
            </Card>
          </Grid>

          {/* Параметри */}
          <Grid item xs={12}>
            <Card sx={{ p: 2.5 }}>
              <Typography variant="subtitle1" fontWeight={700} mb={2} color="primary.main">Параметри посилки</Typography>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={3}>
                  <TextField label="Вага" fullWidth required type="number"
                    value={form.weight} onChange={s('weight')}
                    inputProps={{ min: 0.1, step: 0.1 }}
                    InputProps={{ endAdornment: <InputAdornment position="end">кг</InputAdornment> }}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField label="Ціна доставки" fullWidth disabled
                    value={price ? `${price} ₴` : '—'}
                    helperText="30 грн + 15 грн/кг"
                    sx={{ '& input': { fontWeight: 700, color: '#16A34A' } }}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField select label="Тип оплати" fullWidth value={form.payment_type} onChange={s('payment_type')}>
                    <MenuItem value="prepaid">Передоплата</MenuItem>
                    <MenuItem value="cash_on_delivery">При отриманні</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} sm={3} />
                <Grid item xs={12}>
                  <TextField label="Опис вмісту" fullWidth multiline rows={2}
                    value={form.description} onChange={s('description')} />
                </Grid>
              </Grid>
            </Card>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button variant="contained" type="submit" startIcon={<SaveRounded />} disabled={loading} size="large">
            {loading ? <CircularProgress size={20} color="inherit" /> : 'Зберегти посилку'}
          </Button>
          <Button variant="outlined" onClick={() => navigate('/shipments')}>Скасувати</Button>
        </Box>
      </Box>
    </Box>
  )
}
