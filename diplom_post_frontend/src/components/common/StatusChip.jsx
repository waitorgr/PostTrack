import Chip from '@mui/material/Chip'
import {
  SHIPMENT_STATUS_LABELS,
  SHIPMENT_STATUS_COLORS,
} from '../../utils/statusConfig'

const COLOR_MAP = {
  default: 'default',
  info: 'info',
  warning: 'warning',
  success: 'success',
  error: 'error',
}

export default function StatusChip({
  status,
  labels = SHIPMENT_STATUS_LABELS,
  colors = SHIPMENT_STATUS_COLORS,
  size = 'small',
}) {
  return (
    <Chip
      label={labels[status] || status || '—'}
      color={COLOR_MAP[colors[status]] || 'default'}
      size={size}
      variant="filled"
    />
  )
}