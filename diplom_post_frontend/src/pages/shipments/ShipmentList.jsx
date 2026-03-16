import { useEffect, useState } from 'react'
import { Box, Card, Table, TableBody, TableCell, TableHead, TableRow,
  Typography, TextField, MenuItem, Button, Chip, CircularProgress, Pagination } from '@mui/material'
import { AddRounded, SearchRounded } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { apiGetShipments } from '../../api/shipments'
import StatusChip from '../../components/common/StatusChip'
import { fDateTime, STATUS_LABELS } from '../../utils/formatters'
import { useAuthStore } from '../../store/authStore'

const STATUSES = ['', 'accepted', 'picked_up_by_driver', 'in_transit', 'arrived_at_facility',
  'sorted', 'out_for_delivery', 'available_for_pickup', 'delivered', 'cancelled', 'returned']

export default function ShipmentList() {
  const [items, setItems] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const canCreate = ['postal_worker', 'admin'].includes(user?.role)

  const load = (p = page) => {
    setLoading(true)
    apiGetShipments({ page: p, search, status: status || undefined })
      .then(r => { setItems(r.results || []); setCount(r.count || 0) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1); setPage(1) }, [search, status])

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={800} color="primary.main">Посилки</Typography>
          <Typography variant="body2" color="text.secondary">Всього: {count}</Typography>
        </Box>
        {canCreate && (
          <Button variant="contained" startIcon={<AddRounded />} onClick={() => navigate('/shipments/new')}>
            Нова посилка
          </Button>
        )}
      </Box>

      <Card>
        <Box sx={{ p: 2, display: 'flex', gap: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <TextField size="small" placeholder="Пошук за трекінгом..." value={search}
            onChange={e => setSearch(e.target.value)}
            InputProps={{ startAdornment: <SearchRounded sx={{ color: 'text.secondary', mr: 0.5, fontSize: 18 }} /> }}
            sx={{ width: 260 }}
          />
          <TextField select size="small" value={status} onChange={e => setStatus(e.target.value)} sx={{ width: 200 }}>
            <MenuItem value="">Всі статуси</MenuItem>
            {STATUSES.slice(1).map(s => <MenuItem key={s} value={s}>{STATUS_LABELS[s]}</MenuItem>)}
          </TextField>
        </Box>

        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Трекінг-номер</TableCell>
              <TableCell>Відправник</TableCell>
              <TableCell>Отримувач</TableCell>
              <TableCell>Звідки → Куди</TableCell>
              <TableCell>Вага</TableCell>
              <TableCell>Ціна</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Дата</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={8} align="center" sx={{ py: 4 }}><CircularProgress size={28} /></TableCell></TableRow>}
            {!loading && items.length === 0 && (
              <TableRow><TableCell colSpan={8} align="center" sx={{ py: 4, color: 'text.secondary' }}>Посилок не знайдено</TableCell></TableRow>
            )}
            {!loading && items.map(s => (
              <TableRow key={s.id} sx={{ cursor: 'pointer' }} onClick={() => navigate(`/shipments/${s.id}`)}>
                <TableCell>
                  <Typography variant="body2" fontFamily="JetBrains Mono, monospace" fontWeight={500} color="primary.main" fontSize="0.8rem">
                    {s.tracking_number}
                  </Typography>
                </TableCell>
                <TableCell><Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>{s.sender_full_name}</Typography></TableCell>
                <TableCell><Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>{s.receiver_full_name}</Typography></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary" noWrap>{s.origin_name} → {s.destination_name}</Typography></TableCell>
                <TableCell><Typography variant="body2">{s.weight} кг</Typography></TableCell>
                <TableCell><Typography variant="body2" fontWeight={600}>{s.price} ₴</Typography></TableCell>
                <TableCell><StatusChip status={s.status} /></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{fDateTime(s.created_at)}</Typography></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {count > 20 && (
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
            <Pagination count={Math.ceil(count / 20)} page={page} onChange={(_, p) => { setPage(p); load(p) }} color="primary" />
          </Box>
        )}
      </Card>
    </Box>
  )
}
