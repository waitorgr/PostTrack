import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Card, Grid, Typography, Button, Chip, Divider, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, CircularProgress, Alert } from '@mui/material'
import { ArrowBackRounded, CancelRounded, CheckCircleRounded,
  PaymentRounded, PictureAsPdfRounded, LocalShippingRounded } from '@mui/icons-material'
import { apiGetShipment, apiCancelShipment, apiConfirmDelivery, apiConfirmPayment } from '../../api/shipments'
import { apiGetEvents } from '../../api/tracking'
import { downloadReceipt, downloadDelivery, downloadPayment } from '../../api/reports'
import { useAuthStore } from '../../store/authStore'
import StatusChip from '../../components/common/StatusChip'
import { fDateTime, STATUS_LABELS } from '../../utils/formatters'
import toast from 'react-hot-toast'

const InfoRow = ({ label, value }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.8, borderBottom: '1px solid #F1F5F9' }}>
    <Typography variant="body2" color="text.secondary">{label}</Typography>
    <Typography variant="body2" fontWeight={600} textAlign="right" maxWidth="60%">{value || '—'}</Typography>
  </Box>
)

export default function ShipmentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [shipment, setShipment] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [cancelDialog, setCancelDialog] = useState(false)
  const [cancelReason, setCancelReason] = useState('')
  const [acting, setActing] = useState(false)

  const load = () => {
    Promise.all([apiGetShipment(id), apiGetEvents(id)])
      .then(([sh, ev]) => { setShipment(sh); setEvents(ev.results || ev) })
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [id])

  const isPostal = ['postal_worker','admin'].includes(user?.role)
  const canCancel = isPostal && !['delivered','cancelled','returned'].includes(shipment?.status)
  const canConfirmDelivery = isPostal && !['delivered','cancelled','returned'].includes(shipment?.status)
  const canConfirmPayment = isPostal && shipment?.payment && !shipment.payment.is_paid

  const doCancel = async () => {
    setActing(true)
    try { await apiCancelShipment(id, cancelReason); toast.success('Скасовано'); setCancelDialog(false); load() }
    catch { toast.error('Помилка') } finally { setActing(false) }
  }
  const doDelivery = async () => {
    setActing(true)
    try { await apiConfirmDelivery(id); toast.success('Доставку підтверджено'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Помилка') } finally { setActing(false) }
  }
  const doPayment = async () => {
    setActing(true)
    try { await apiConfirmPayment(id); toast.success('Оплату підтверджено'); load() }
    catch { toast.error('Помилка') } finally { setActing(false) }
  }

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', pt: 8 }}><CircularProgress /></Box>
  if (!shipment) return <Alert severity="error">Посилку не знайдено</Alert>

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Button startIcon={<ArrowBackRounded />} onClick={() => navigate('/shipments')}>Назад</Button>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Typography variant="h6" fontWeight={800} fontFamily="JetBrains Mono, monospace" color="primary.main">
              {shipment.tracking_number}
            </Typography>
            <StatusChip status={shipment.status} />
          </Box>
          <Typography variant="caption" color="text.secondary">{fDateTime(shipment.created_at)} · {shipment.created_by_name}</Typography>
        </Box>

        {/* Дії */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {canConfirmDelivery && (
            <Button variant="contained" color="success" size="small" startIcon={<CheckCircleRounded />}
              onClick={doDelivery} disabled={acting}>Підтвердити доставку</Button>
          )}
          {canConfirmPayment && (
            <Button variant="outlined" color="success" size="small" startIcon={<PaymentRounded />}
              onClick={doPayment} disabled={acting}>Підтвердити оплату</Button>
          )}
          {canCancel && (
            <Button variant="outlined" color="error" size="small" startIcon={<CancelRounded />}
              onClick={() => setCancelDialog(true)}>Скасувати</Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Відправник */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="overline" color="text.secondary" fontSize="0.68rem">Відправник</Typography>
            <InfoRow label="ПІБ" value={shipment.sender_full_name} />
            <InfoRow label="Телефон" value={shipment.sender_phone} />
            {shipment.sender_email && <InfoRow label="Email" value={shipment.sender_email} />}
            <InfoRow label="Відділення" value={`${shipment.origin_name} (${shipment.origin_city})`} />
          </Card>
        </Grid>

        {/* Отримувач */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="overline" color="text.secondary" fontSize="0.68rem">Отримувач</Typography>
            <InfoRow label="ПІБ" value={shipment.receiver_full_name} />
            <InfoRow label="Телефон" value={shipment.receiver_phone} />
            {shipment.receiver_email && <InfoRow label="Email" value={shipment.receiver_email} />}
            <InfoRow label="Відділення" value={`${shipment.destination_name} (${shipment.destination_city})`} />
          </Card>
        </Grid>

        {/* Параметри */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="overline" color="text.secondary" fontSize="0.68rem">Параметри</Typography>
            <InfoRow label="Вага" value={`${shipment.weight} кг`} />
            <InfoRow label="Ціна" value={`${shipment.price} ₴`} />
            <InfoRow label="Оплата" value={shipment.payment_type_display} />
            <InfoRow label="Статус оплати" value={shipment.payment?.is_paid ? '✅ Оплачено' : '⏳ Не оплачено'} />
            {shipment.description && <InfoRow label="Опис" value={shipment.description} />}
          </Card>
        </Grid>

        {/* PDF звіти */}
        {isPostal && (
          <Grid item xs={12}>
            <Card sx={{ p: 2.5 }}>
              <Typography variant="subtitle2" fontWeight={700} mb={1.5}>PDF звіти</Typography>
              <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                <Button size="small" variant="outlined" startIcon={<PictureAsPdfRounded />}
                  onClick={() => downloadReceipt(id).catch(() => toast.error('Помилка'))}>
                  Квитанція прийому
                </Button>
                <Button size="small" variant="outlined" startIcon={<PictureAsPdfRounded />}
                  onClick={() => downloadDelivery(id).catch(() => toast.error('Помилка'))}>
                  Підтвердження доставки
                </Button>
                <Button size="small" variant="outlined" startIcon={<PictureAsPdfRounded />}
                  onClick={() => downloadPayment(id).catch(() => toast.error('Помилка'))}>
                  Звіт оплати
                </Button>
              </Box>
            </Card>
          </Grid>
        )}

        {/* Хронологія */}
        <Grid item xs={12}>
          <Card sx={{ p: 2.5 }}>
            <Typography variant="subtitle2" fontWeight={700} mb={2}>Хронологія подій</Typography>
            {events.length === 0 && <Typography variant="body2" color="text.secondary">Немає подій</Typography>}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {events.map((ev, i) => (
                <Box key={ev.id} sx={{ display: 'flex', gap: 2 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <Box sx={{
                      width: 10, height: 10, borderRadius: '50%', mt: 0.7, flexShrink: 0,
                      bgcolor: i === 0 ? 'primary.main' : '#CBD5E1',
                      border: i === 0 ? '2px solid #1B3F7A' : 'none',
                    }} />
                    {i < events.length - 1 && <Box sx={{ width: 2, flex: 1, bgcolor: '#E2E8F0', my: 0.3 }} />}
                  </Box>
                  <Box sx={{ pb: 2, flex: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Typography variant="body2" fontWeight={600}>{ev.event_type_display}</Typography>
                      <Typography variant="caption" color="text.secondary" ml={2} flexShrink={0}>{fDateTime(ev.created_at)}</Typography>
                    </Box>
                    {ev.location_name && <Typography variant="caption" color="text.secondary">{ev.location_name}, {ev.location_city}</Typography>}
                    {ev.note && <Typography variant="caption" display="block" color="text.secondary">{ev.note}</Typography>}
                    {ev.created_by_name && <Typography variant="caption" display="block" color="text.secondary">Хто: {ev.created_by_name}</Typography>}
                  </Box>
                </Box>
              ))}
            </Box>
          </Card>
        </Grid>
      </Grid>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialog} onClose={() => setCancelDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle fontWeight={700}>Скасувати посилку?</DialogTitle>
        <DialogContent>
          <TextField label="Причина скасування" fullWidth multiline rows={3} sx={{ mt: 1 }}
            value={cancelReason} onChange={e => setCancelReason(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialog(false)}>Відмінити</Button>
          <Button variant="contained" color="error" onClick={doCancel} disabled={acting}>Скасувати посилку</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
