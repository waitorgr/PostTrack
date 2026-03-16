import { useEffect, useState } from 'react'
import { Box, Card, Typography, Table, TableHead, TableRow, TableCell,
  TableBody, Button, CircularProgress, Chip } from '@mui/material'
import { DownloadRounded } from '@mui/icons-material'
import { apiGetShipments } from '../../api/shipments'
import { downloadPayment } from '../../api/reports'
import { fDateTime, STATUS_LABELS, STATUS_COLORS } from '../../utils/formatters'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export default function MyShipments() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    apiGetShipments().then(r => setItems(r.results || r)).finally(() => setLoading(false))
  }, [])

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} color="primary.main" mb={3}>Мої відправлення</Typography>
      <Card>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Трекінг-номер</TableCell>
              <TableCell>Куди</TableCell>
              <TableCell>Вага</TableCell>
              <TableCell>Ціна</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Дата</TableCell>
              <TableCell>Квитанція</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && <TableRow><TableCell colSpan={7} align="center" sx={{ py: 4 }}><CircularProgress size={28} /></TableCell></TableRow>}
            {!loading && items.length === 0 && (
              <TableRow><TableCell colSpan={7} align="center" sx={{ py: 4, color: 'text.secondary' }}>Відправлень немає</TableCell></TableRow>
            )}
            {!loading && items.map(s => (
              <TableRow key={s.id}>
                <TableCell>
                  <Typography variant="body2" fontFamily="JetBrains Mono, monospace" fontWeight={600} color="primary.main" fontSize="0.8rem">
                    {s.tracking_number}
                  </Typography>
                </TableCell>
                <TableCell><Typography variant="body2">{s.destination_name}</Typography></TableCell>
                <TableCell>{s.weight} кг</TableCell>
                <TableCell fontWeight={600}>{s.price} ₴</TableCell>
                <TableCell>
                  <Chip label={STATUS_LABELS[s.status] || s.status} color={STATUS_COLORS[s.status] || 'default'}
                    size="small" sx={{ fontWeight: 600, borderRadius: '6px' }} />
                </TableCell>
                <TableCell><Typography variant="caption" color="text.secondary">{fDateTime(s.created_at)}</Typography></TableCell>
                <TableCell>
                  {s.payment?.is_paid && (
                    <Button size="small" startIcon={<DownloadRounded />} variant="outlined"
                      onClick={() => downloadPayment(s.id).catch(() => toast.error('Помилка'))}>
                      PDF
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </Box>
  )
}
