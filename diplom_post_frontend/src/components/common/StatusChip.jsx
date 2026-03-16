import { Chip } from '@mui/material'
import { STATUS_LABELS, STATUS_COLORS } from '../../utils/formatters'

export default function StatusChip({ status, size = 'small' }) {
  return (
    <Chip
      label={STATUS_LABELS[status] || status}
      color={STATUS_COLORS[status] || 'default'}
      size={size}
      sx={{ fontWeight: 600, borderRadius: '6px' }}
    />
  )
}
