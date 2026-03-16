import { useEffect, useState } from 'react'
import { Box, Card, Table, TableBody, TableCell, TableHead, TableRow,
  Typography, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, MenuItem, Collapse, IconButton, CircularProgress } from '@mui/material'
import { AddRounded, ExpandMoreRounded, ExpandLessRounded, PictureAsPdfRounded } from '@mui/icons-material'
import { apiGetGroups, apiCreateGroup, apiAddShipment, apiRemoveShipment, apiMarkReady, apiDepart, apiArrive } from '../../api/dispatch'
import { apiGetLocations } from '../../api/locations'
import { apiGetWorkers } from '../../api/auth'
import { downloadDispatchDepart, downloadDispatchArrive } from '../../api/reports'
import { fDateTime, DISPATCH_STATUS_LABELS, DISPATCH_STATUS_COLORS } from '../../utils/formatters'
import toast from 'react-hot-toast'

const StatusChip = ({ status }) => (
  <Chip label={DISPATCH_STATUS_LABELS[status] || status} color={DISPATCH_STATUS_COLORS[status] || 'default'}
    size="small" sx={{ fontWeight: 600, borderRadius: '6px' }} />
)

function GroupRow({ group: init, onRefresh }) {
  const [open, setOpen] = useState(false)
  const [group, setGroup] = useState(init)
  const [adding, setAdding] = useState('')
  const [acting, setActing] = useState(false)

  useEffect(() => setGroup(init), [init])

  const act = async (fn, msg) => {
    setActing(true)
    try { const g = await fn(); setGroup(g); toast.success(msg) }
    catch (e) { toast.error(e.response?.data?.detail || 'Помилка') }
    finally { setActing(false) }
  }

  const addShipment = async () => {
    if (!adding.trim()) return
    act(() => apiAddShipment(group.id, adding.trim().toUpperCase()), 'Посилку додано')
    setAdding('')
  }

  return (
    <>
      <TableRow sx={{ cursor: 'pointer', '& td': { borderBottom: open ? '0' : undefined } }}
        onClick={() => setOpen(p => !p)}>
        <TableCell>
          <Typography variant="body2" fontFamily="JetBrains Mono, monospace" fontWeight={600} color="primary.main">
            {group.code}
          </Typography>
        </TableCell>
        <TableCell><StatusChip status={group.status} /></TableCell>
        <TableCell><Typography variant="body2">{group.origin_name}</Typography></TableCell>
        <TableCell><Typography variant="body2">{group.destination_name}</Typography></TableCell>
        <TableCell><Typography variant="body2">{group.driver_name || '—'}</Typography></TableCell>
        <TableCell><Chip label={group.shipment_count} size="small" variant="outlined" /></TableCell>
        <TableCell><Typography variant="caption" color="text.secondary">{fDateTime(group.created_at)}</Typography></TableCell>
        <TableCell align="right">
          <IconButton size="small">{open ? <ExpandLessRounded /> : <ExpandMoreRounded />}</IconButton>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={8} sx={{ p: 0, border: 0 }}>
          <Collapse in={open}>
            <Box sx={{ p: 2, bgcolor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
              {/* Посилки */}
              {group.items?.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" fontWeight={700} color="text.secondary" mb={1} display="block">ПОСИЛКИ</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {group.items.map(item => (
                      <Chip key={item.id}
                        label={item.shipment_detail?.tracking_number || item.shipment}
                        size="small" variant="outlined"
                        onDelete={['forming','ready'].includes(group.status) ? () =>
                          act(() => apiRemoveShipment(group.id, item.shipment_detail?.tracking_number), 'Видалено') : undefined}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Додати посилку */}
              {['forming','ready'].includes(group.status) && (
                <Box sx={{ display: 'flex', gap: 1, mb: 2, maxWidth: 400 }}>
                  <TextField size="small" placeholder="Трекінг-номер" value={adding}
                    onChange={e => setAdding(e.target.value.toUpperCase())}
                    inputProps={{ style: { fontFamily: 'JetBrains Mono, monospace' } }}
                    sx={{ flex: 1 }} />
                  <Button size="small" variant="outlined" onClick={addShipment}>Додати</Button>
                </Box>
              )}

              {/* Дії */}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {group.status === 'forming' && (
                  <Button size="small" variant="contained" onClick={() => act(() => apiMarkReady(group.id), 'Готово')} disabled={acting}>
                    Позначити готовим
                  </Button>
                )}
                {group.status === 'ready' && (
                  <Button size="small" variant="contained" color="success"
                    onClick={() => act(() => apiDepart(group.id), 'Відправлено')} disabled={acting}>
                    Підтвердити відправку
                  </Button>
                )}
                {group.status === 'in_transit' && (
                  <Button size="small" variant="contained" color="info"
                    onClick={() => act(() => apiArrive(group.id), 'Прибуття підтверджено')} disabled={acting}>
                    Підтвердити прибуття
                  </Button>
                )}
                {['in_transit','arrived','completed'].includes(group.status) && (
                  <>
                    <Button size="small" variant="outlined" startIcon={<PictureAsPdfRounded />}
                      onClick={() => downloadDispatchDepart(group.id).catch(() => toast.error('Помилка'))}>
                      Акт передачі
                    </Button>
                    {group.status !== 'in_transit' && (
                      <Button size="small" variant="outlined" startIcon={<PictureAsPdfRounded />}
                        onClick={() => downloadDispatchArrive(group.id).catch(() => toast.error('Помилка'))}>
                        Акт прийому
                      </Button>
                    )}
                  </>
                )}
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  )
}

export default function DispatchList() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [locations, setLocations] = useState([])
  const [drivers, setDrivers] = useState([])
  const [form, setForm] = useState({ destination: '', driver: '' })

  const load = () => {
    setLoading(true)
    apiGetGroups().then(r => setGroups(r.results || r)).finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    apiGetLocations().then(r => setLocations(r.results || r))
    apiGetWorkers({ role: 'driver' }).then(r => setDrivers(r.results || r))
  }, [])

  const create = async () => {
    try {
      await apiCreateGroup({ destination: form.destination, driver: form.driver || null })
      toast.success('Групу створено')
      setCreateOpen(false)
      setForm({ destination: '', driver: '' })
      load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Помилка') }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">Dispatch групи</Typography>
          <Typography variant="body2" color="text.secondary">Групи посилок вашої локації</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddRounded />} onClick={() => setCreateOpen(true)}>
          Нова група
        </Button>
      </Box>

      <Card>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Код групи</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Звідки</TableCell>
              <TableCell>Куди</TableCell>
              <TableCell>Водій</TableCell>
              <TableCell>Посилок</TableCell>
              <TableCell>Створено</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={8} align="center" sx={{ py: 4 }}><CircularProgress size={28} /></TableCell></TableRow>}
            {!loading && groups.length === 0 && (
              <TableRow><TableCell colSpan={8} align="center" sx={{ py: 4, color: 'text.secondary' }}>Груп немає</TableCell></TableRow>
            )}
            {!loading && groups.map(g => <GroupRow key={g.id} group={g} onRefresh={load} />)}
          </TableBody>
        </Table>
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle fontWeight={700}>Нова Dispatch група</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField select label="Куди (локація призначення)" fullWidth required
            value={form.destination} onChange={e => setForm(p => ({ ...p, destination: e.target.value }))}>
            {locations.map(l => <MenuItem key={l.id} value={l.id}>{l.name} — {l.city}</MenuItem>)}
          </TextField>
          <TextField select label="Водій" fullWidth
            value={form.driver} onChange={e => setForm(p => ({ ...p, driver: e.target.value }))}>
            <MenuItem value="">Без водія (призначити пізніше)</MenuItem>
            {drivers.map(d => <MenuItem key={d.id} value={d.id}>{d.last_name} {d.first_name}</MenuItem>)}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Скасувати</Button>
          <Button variant="contained" onClick={create} disabled={!form.destination}>Створити</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
