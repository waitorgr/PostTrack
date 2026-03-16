import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box, Card, TextField, Button, Typography, InputAdornment,
  IconButton, CircularProgress, Alert,
} from '@mui/material'
import { VisibilityRounded, VisibilityOffRounded, LocalShippingRounded } from '@mui/icons-material'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPwd, setShowPwd] = useState(false)
  const [error, setError] = useState('')
  const { login, loading } = useAuthStore()
  const navigate = useNavigate()

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    const res = await login(form.username, form.password)
    if (res.ok) navigate('/')
    else setError(res.error)
  }

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0F172A 0%, #1B3F7A 50%, #1e3a8a 100%)',
      p: 2,
    }}>
      {/* Background pattern */}
      <Box sx={{
        position: 'fixed', inset: 0, opacity: 0.04,
        backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)',
        backgroundSize: '28px 28px', pointerEvents: 'none',
      }} />

      <Card sx={{ width: '100%', maxWidth: 400, p: 4, position: 'relative', zIndex: 1 }}>
        {/* Logo */}
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3.5 }}>
          <Box sx={{
            width: 52, height: 52, borderRadius: '14px', mb: 2,
            background: 'linear-gradient(135deg, #1B3F7A 0%, #2563EB 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(37,99,235,.4)',
          }}>
            <LocalShippingRounded sx={{ color: 'white', fontSize: 26 }} />
          </Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">PostTrack</Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>Система управління відправленнями</Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}

        <Box component="form" onSubmit={handle} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Логін" fullWidth required autoFocus
            value={form.username}
            onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
          />
          <TextField
            label="Пароль" fullWidth required
            type={showPwd ? 'text' : 'password'}
            value={form.password}
            onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPwd(p => !p)} edge="end" size="small">
                    {showPwd ? <VisibilityOffRounded /> : <VisibilityRounded />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Button type="submit" variant="contained" fullWidth size="large" disabled={loading}
            sx={{ mt: 0.5, py: 1.3 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Увійти'}
          </Button>
        </Box>

        <Box sx={{ mt: 2.5, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Відстежити посилку без входу?{' '}
            <Link to="/track" style={{ color: '#2563EB', fontWeight: 600, textDecoration: 'none' }}>
              Перевірити
            </Link>
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Ще немає акаунту?{' '}
            <Link to="/register" style={{ color: '#2563EB', fontWeight: 600, textDecoration: 'none' }}>
              Зареєструватись
            </Link>
          </Typography>
        </Box>
      </Card>
    </Box>
  )
}
