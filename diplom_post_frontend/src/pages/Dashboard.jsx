import { useEffect, useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, Chip, Table, TableBody,
  TableCell, TableHead, TableRow, CircularProgress, Button } from '@mui/material'
import { LocalShippingRounded, CheckCircleRounded, CancelRounded,
  HourglassEmptyRounded, TrendingUpRounded } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { apiGetShipments } from '../api/shipments'
import { useAuthStore } from '../store/authStore'
import StatusChip from '../components/common/StatusChip'
import { fDateTime } from '../utils/formatters'

const StatCard = ({ icon, label, value, color, sub }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent sx={{ p: 2.5 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="overline" color="text.secondary" sx={{ fontSize: '0.7rem' }}>{label}</Typography>
          <Typography variant="h4" fontWeight={800} color={color} sx={{ mt: 0.5, lineHeight: 1 }}>{value}</Typography>
          {sub && <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>{sub}</Typography>}
        </Box>
        <Box sx={{
          width: 44, height: 44, borderRadius: '11px',
          background: `${color}18`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
)

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    apiGetShipments({ page_size: 100 }).then(res => {
      const items = res.results || res
      setData(items)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', pt: 8 }}><CircularProgress /></Box>

  const all = data || []
  const delivered = all.filter(s => s.status === 'delivered').length
  const inProgress = all.filter(s => !['delivered','cancelled','returned'].includes(s.status)).length
  const cancelled = all.filter(s => s.status === 'cancelled').length
  const recent = [...all].slice(0, 8)

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={800} color="primary.main">Дашборд</Typography>
        <Typography variant="body2" color="text.secondary">
          {user?.location_name || 'Загальний огляд'} · {new Date().toLocaleDateString('uk-UA', { weekday:'long', day:'numeric', month:'long' })}
        </Typography>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <StatCard icon={<LocalShippingRounded sx={{ color: '#1B3F7A' }} />} label="Всього посилок" value={all.length} color="#1B3F7A" />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard icon={<HourglassEmptyRounded sx={{ color: '#D97706' }} />} label="В процесі" value={inProgress} color="#D97706" />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard icon={<CheckCircleRounded sx={{ color: '#16A34A' }} />} label="Доставлено" value={delivered} color="#16A34A" />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard icon={<CancelRounded sx={{ color: '#DC2626' }} />} label="Скасовано" value={cancelled} color="#DC2626" />
        </Grid>
      </Grid>

      <Card>
        <Box sx={{ px: 2.5, py: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle1" fontWeight={700}>Останні посилки</Typography>
          <Button size="small" onClick={() => navigate('/shipments')}>Всі посилки</Button>
        </Box>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Трекінг-номер</TableCell>
              <TableCell>Відправник</TableCell>
              <TableCell>Отримувач</TableCell>
              <TableCell>Напрямок</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Дата</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {recent.length === 0 && (
              <TableRow><TableCell colSpan={6} align="center" sx={{ py: 4, color: 'text.secondary' }}>Немає посилок</TableCell></TableRow>
            )}
            {recent.map(s => (
              <TableRow key={s.id} sx={{ cursor: 'pointer' }} onClick={() => navigate(`/shipments/${s.id}`)}>
                <TableCell>
                  <Typography variant="body2" fontFamily="JetBrains Mono, monospace" fontWeight={500} color="primary.main">
                    {s.tracking_number}
                  </Typography>
                </TableCell>
                <TableCell><Typography variant="body2">{s.sender_full_name}</Typography></TableCell>
                <TableCell><Typography variant="body2">{s.receiver_full_name}</Typography></TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary">{s.origin_name} → {s.destination_name}</Typography>
                </TableCell>
                <TableCell><StatusChip status={s.status} /></TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{fDateTime(s.created_at)}</Typography></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </Box>
  )
}
