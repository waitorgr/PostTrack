import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Box, Card, TextField, Button, Typography, Alert, Grid, CircularProgress } from '@mui/material'
import { LocalShippingRounded } from '@mui/icons-material'
import { apiRegisterCustomer } from '../api/auth'

export default function Register() {
  const [form, setForm] = useState({ username:'', first_name:'', last_name:'', patronymic:'', phone:'', email:'', password:'' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const set = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }))

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await apiRegisterCustomer(form)
      navigate('/login')
    } catch (err) {
      const d = err.response?.data
      setError(d ? Object.values(d).flat().join(' ') : 'Помилка реєстрації')
    } finally { setLoading(false) }
  }

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0F172A 0%, #1B3F7A 50%, #1e3a8a 100%)', p: 2,
    }}>
      <Card sx={{ width: '100%', maxWidth: 480, p: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
          <Box sx={{
            width: 48, height: 48, borderRadius: '12px', mb: 1.5,
            background: 'linear-gradient(135deg, #1B3F7A 0%, #2563EB 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <LocalShippingRounded sx={{ color: 'white', fontSize: 24 }} />
          </Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">Реєстрація</Typography>
          <Typography variant="body2" color="text.secondary">Клієнтський акаунт PostTrack</Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}

        <Box component="form" onSubmit={handle}>
          <Grid container spacing={2}>
            <Grid item xs={12}><TextField label="Логін" fullWidth required value={form.username} onChange={set('username')} /></Grid>
            <Grid item xs={6}><TextField label="Прізвище" fullWidth required value={form.last_name} onChange={set('last_name')} /></Grid>
            <Grid item xs={6}><TextField label="Ім'я" fullWidth required value={form.first_name} onChange={set('first_name')} /></Grid>
            <Grid item xs={12}><TextField label="По-батькові" fullWidth required value={form.patronymic} onChange={set('patronymic')} /></Grid>
            <Grid item xs={12}><TextField label="Телефон" fullWidth required placeholder="+380XXXXXXXXX" value={form.phone} onChange={set('phone')} /></Grid>
            <Grid item xs={12}><TextField label="Email" type="email" fullWidth required value={form.email} onChange={set('email')} /></Grid>
            <Grid item xs={12}><TextField label="Пароль" type="password" fullWidth required value={form.password} onChange={set('password')} /></Grid>
          </Grid>
          <Button type="submit" variant="contained" fullWidth size="large" disabled={loading} sx={{ mt: 3, py: 1.3 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Зареєструватись'}
          </Button>
        </Box>

        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Вже є акаунт?{' '}
            <Link to="/login" style={{ color: '#2563EB', fontWeight: 600, textDecoration: 'none' }}>Увійти</Link>
          </Typography>
        </Box>
      </Card>
    </Box>
  )
}
