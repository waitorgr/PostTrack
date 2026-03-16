import { useEffect, useState } from 'react'
import { Box, Card, Table, TableBody, TableCell, TableHead, TableRow,
  Typography, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, CircularProgress } from '@mui/material'
import { AddRounded } from '@mui/icons-material'
import { apiGetRoutes, apiCreateRoute, apiConfirmRoute, apiStartRoute, apiCompleteRoute } from '../../api/logistics'
import { apiGetGroups } from '../../api/dispatch'
import { apiGetWorkers } from '../../api/auth'
import { fDateTime, ROUTE_STATUS_LABELS, ROUTE_STATUS_COLORS } from '../../utils/formatters'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

const StatusChip = ({ status }) => (
  <Chip label={ROUTE_STATUS_LABELS[status] || status} color={ROUTE_STATUS_COLORS[status] || 'default'}
    size="small" sx={{ fontWeight: 600, borderRadius: '6px' }} />
)

export default function RouteList() {
  const { user } = useAuthStore()
  const [routes, setRoutes] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [drivers, setDrivers] = useState([])
  const [groups, setGroups] = useState([])
  const [form, setForm] = useState({ driver: '', dispatch_group: '', destination: '', scheduled_departure: '', notes: '' })
  const [acting, setActing] = useState(null)
  const isLogist = ['logist', 'admin'].includes(user?.role)

  const load = () => {
    setLoading(true)
    apiGetRoutes().then(r => setRoutes(r.results || r)).finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    if (isLogist) {
      apiGetWorkers({ role: 'driver' }).then(r => setDrivers(r.results || r))
      apiGetGroups({ status: 'ready' }).then(r => setGroups(r.results || r))
    }
  }, [])

  const create = async () => {
    try {
      await apiCreateRoute({ ...form, destination: parseInt(form.destination) || undefined })
      toast.success('Маршрут створено'); setCreateOpen(false)
      setForm({ driver: '', dispatch_group: '', destination: '', scheduled_departure: '', notes: '' })
      load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Помилка') }
  }

  const act = async (fn, msg, id) => {
    setActing(id)
    try { await fn(); toast.success(msg); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Помилка') }
    finally { setActing(null) }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">Маршрути</Typography>
          <Typography variant="body2" color="text.secondary">{isLogist ? 'Управління маршрутами водіїв' : 'Мої маршрути'}</Typography>
        </Box>
        {isLogist && (
          <Button variant="contained" startIcon={<AddRounded />} onClick={() => setCreateOpen(true)}>
            Новий маршрут
          </Button>
        )}
      </Box>

      <Card>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Dispatch група</TableCell>
              <TableCell>Водій</TableCell>
              <TableCell>Звідки</TableCell>
              <TableCell>Куди</TableCell>
              <TableCell>Виїзд</TableCell>
              <TableCell>Статус</TableCell>
              {isLogist && <TableCell>Дії</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={7} align="center" sx={{ py: 4 }}><CircularProgress size={28} /></TableCell></TableRow>}
            {!loading && routes.length === 0 && (
              <TableRow><TableCell colSpan={7} align="center" sx={{ py: 4, color: 'text.secondary' }}>Маршрутів немає</TableCell></TableRow>
            )}
            {!loading && routes.map(r => (
              <TableRow key={r.id}>
                <TableCell>
                  <Typography variant="body2" fontFamily="JetBrains Mono, monospace" fontWeight={600} color="primary.main">
                    {r.group_code}
                  </Typography>
                </TableCell>
                <TableCell><Typography variant="body2">{r.driver_name}</Typography></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{r.origin_name}</Typography></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{r.destination_name}</Typography></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{fDateTime(r.scheduled_departure)}</Typography></TableCell>
                <TableCell><StatusChip status={r.status} /></TableCell>
                {isLogist && (
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {r.status === 'draft' && (
                        <Button size="small" variant="outlined" disabled={acting === r.id}
                          onClick={() => act(() => apiConfirmRoute(r.id), 'Підтверджено', r.id)}>
                          Підтвердити
                        </Button>
                      )}
                      {r.status === 'confirmed' && (
                        <Button size="small" variant="outlined" color="success" disabled={acting === r.id}
                          onClick={() => act(() => apiStartRoute(r.id), 'Виконується', r.id)}>
                          Почати
                        </Button>
                      )}
                      {r.status === 'in_progress' && (
                        <Button size="small" variant="contained" color="success" disabled={acting === r.id}
                          onClick={() => act(() => apiCompleteRoute(r.id), 'Завершено', r.id)}>
                          Завершити
                        </Button>
                      )}
                    </Box>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={700}>Новий маршрут</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField select label="Водій" fullWidth required value={form.driver}
            onChange={e => setForm(p => ({ ...p, driver: e.target.value }))}>
            {drivers.map(d => <MenuItem key={d.id} value={d.id}>{d.last_name} {d.first_name} {d.patronymic}</MenuItem>)}
          </TextField>
          <TextField select label="Dispatch група (готова до відправки)" fullWidth required value={form.dispatch_group}
            onChange={e => setForm(p => ({ ...p, dispatch_group: e.target.value }))}>
            {groups.map(g => <MenuItem key={g.id} value={g.id}>{g.code} — {g.origin_name} → {g.destination_name}</MenuItem>)}
          </TextField>
          <TextField label="Запланований час виїзду" type="datetime-local" fullWidth required
            value={form.scheduled_departure} onChange={e => setForm(p => ({ ...p, scheduled_departure: e.target.value }))}
            InputLabelProps={{ shrink: true }} />
          <TextField label="Нотатки для водія" fullWidth multiline rows={2}
            value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Скасувати</Button>
          <Button variant="contained" onClick={create} disabled={!form.driver || !form.dispatch_group}>Створити</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
