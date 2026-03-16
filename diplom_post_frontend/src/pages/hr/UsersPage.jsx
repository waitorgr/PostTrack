import { useEffect, useState } from 'react'
import { Box, Card, Table, TableBody, TableCell, TableHead, TableRow,
  Typography, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, Grid, CircularProgress, IconButton, Tooltip } from '@mui/material'
import { AddRounded, EditRounded, BlockRounded } from '@mui/icons-material'
import { apiGetWorkers, apiCreateWorker, apiUpdateWorker, apiDeleteWorker } from '../../api/auth'
import { apiGetLocations } from '../../api/locations'
import { ROLE_LABELS } from '../../utils/formatters'
import toast from 'react-hot-toast'

const ROLES = ['postal_worker', 'warehouse_worker', 'driver', 'logist', 'hr']

export default function UsersPage() {
  const [workers, setWorkers] = useState([])
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const [dialog, setDialog] = useState(null) // null | 'create' | worker_object
  const [form, setForm] = useState({ username:'', first_name:'', last_name:'', patronymic:'', email:'', phone:'', role:'postal_worker', location:'' })

  const load = () => {
    setLoading(true)
    apiGetWorkers().then(r => setWorkers(r.results || r)).finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    apiGetLocations().then(r => setLocations(r.results || r))
  }, [])

  const openCreate = () => {
    setForm({ username:'', first_name:'', last_name:'', patronymic:'', email:'', phone:'', role:'postal_worker', location:'' })
    setDialog('create')
  }

  const openEdit = (w) => {
    setForm({ first_name: w.first_name, last_name: w.last_name, patronymic: w.patronymic,
      email: w.email, phone: w.phone, role: w.role, location: w.location || '' })
    setDialog(w)
  }

  const save = async () => {
    try {
      if (dialog === 'create') {
        await apiCreateWorker({ ...form, location: form.location || null })
        toast.success('Працівника додано')
      } else {
        await apiUpdateWorker(dialog.id, { ...form, location: form.location || null })
        toast.success('Оновлено')
      }
      setDialog(null); load()
    } catch (e) {
      const d = e.response?.data
      toast.error(d ? Object.values(d).flat().join(' ') : 'Помилка')
    }
  }

  const deactivate = async (w) => {
    try { await apiDeleteWorker(w.id); toast.success('Деактивовано'); load() }
    catch { toast.error('Помилка') }
  }

  const s = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }))

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">Персонал</Typography>
          <Typography variant="body2" color="text.secondary">Управління працівниками системи</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddRounded />} onClick={openCreate}>Додати працівника</Button>
      </Box>

      <Card>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Логін</TableCell>
              <TableCell>ПІБ</TableCell>
              <TableCell>Роль</TableCell>
              <TableCell>Локація</TableCell>
              <TableCell>Телефон</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell align="right">Дії</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={8} align="center" sx={{ py: 4 }}><CircularProgress size={28} /></TableCell></TableRow>}
            {!loading && workers.length === 0 && (
              <TableRow><TableCell colSpan={8} align="center" sx={{ py: 4, color: 'text.secondary' }}>Немає працівників</TableCell></TableRow>
            )}
            {!loading && workers.map(w => (
              <TableRow key={w.id}>
                <TableCell><Typography variant="body2" fontWeight={600}>{w.username}</Typography></TableCell>
                <TableCell><Typography variant="body2">{w.last_name} {w.first_name} {w.patronymic}</Typography></TableCell>
                <TableCell><Chip label={ROLE_LABELS[w.role] || w.role} size="small" variant="outlined" sx={{ fontWeight: 600 }} /></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{w.location_name || '—'}</Typography></TableCell>
                <TableCell><Typography variant="caption">{w.phone}</Typography></TableCell>
                <TableCell><Typography variant="caption">{w.email}</Typography></TableCell>
                <TableCell>
                  <Chip label={w.is_active ? 'Активний' : 'Деактивований'} size="small"
                    color={w.is_active ? 'success' : 'default'} sx={{ fontWeight: 600 }} />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Редагувати">
                    <IconButton size="small" onClick={() => openEdit(w)}><EditRounded fontSize="small" /></IconButton>
                  </Tooltip>
                  {w.is_active && (
                    <Tooltip title="Деактивувати">
                      <IconButton size="small" color="error" onClick={() => deactivate(w)}><BlockRounded fontSize="small" /></IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <Dialog open={!!dialog} onClose={() => setDialog(null)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={700}>{dialog === 'create' ? 'Новий працівник' : 'Редагувати працівника'}</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Grid container spacing={2}>
            {dialog === 'create' && (
              <Grid item xs={12}><TextField label="Логін" fullWidth required value={form.username} onChange={s('username')} /></Grid>
            )}
            <Grid item xs={6}><TextField label="Прізвище" fullWidth required value={form.last_name} onChange={s('last_name')} /></Grid>
            <Grid item xs={6}><TextField label="Ім'я" fullWidth required value={form.first_name} onChange={s('first_name')} /></Grid>
            <Grid item xs={12}><TextField label="По-батькові" fullWidth required value={form.patronymic} onChange={s('patronymic')} /></Grid>
            <Grid item xs={6}><TextField label="Телефон" fullWidth required value={form.phone} onChange={s('phone')} /></Grid>
            <Grid item xs={6}><TextField label="Email" fullWidth required value={form.email} onChange={s('email')} type="email" /></Grid>
            <Grid item xs={6}>
              <TextField select label="Роль" fullWidth required value={form.role} onChange={s('role')}>
                {ROLES.map(r => <MenuItem key={r} value={r}>{ROLE_LABELS[r]}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={6}>
              <TextField select label="Локація" fullWidth value={form.location} onChange={s('location')}>
                <MenuItem value="">Без локації</MenuItem>
                {locations.map(l => <MenuItem key={l.id} value={l.id}>{l.name} ({l.city})</MenuItem>)}
              </TextField>
            </Grid>
            {dialog === 'create' && (
              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Початковий пароль: <strong>adminadmin</strong> (працівник має змінити після першого входу)
                </Typography>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(null)}>Скасувати</Button>
          <Button variant="contained" onClick={save}>Зберегти</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
