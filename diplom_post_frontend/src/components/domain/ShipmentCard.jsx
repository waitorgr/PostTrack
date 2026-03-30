import { Box, Stack, Typography } from '@mui/material'
import Card from '../ui/Card'
import Button from '../ui/Button'
import StatusBadge from './StatusBadge'
import { fDateTime } from '../../utils/formatters'

export default function ShipmentCard({
  shipment,
  actionLabel,
  onAction,
}) {
  if (!shipment) return null

  return (
    <Card>
      <Stack spacing={1.5}>
        <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
          <Typography variant="h6" fontWeight={700}>
            {shipment.tracking_number || '—'}
          </Typography>
          <StatusBadge status={shipment.status} type="shipment" />
        </Box>

        <Typography variant="body2" color="text.secondary">
          {shipment.origin?.name || shipment.origin_name || '—'} →{' '}
          {shipment.destination?.name || shipment.destination_name || '—'}
        </Typography>

        <Typography variant="body2">
          Опис: {shipment.description || '—'}
        </Typography>

        <Typography variant="caption" color="text.secondary">
          Створено: {fDateTime(shipment.created_at)}
        </Typography>

        {onAction && (
          <Box pt={1}>
            <Button onClick={() => onAction(shipment)}>
              {actionLabel || 'Відкрити'}
            </Button>
          </Box>
        )}
      </Stack>
    </Card>
  )
}