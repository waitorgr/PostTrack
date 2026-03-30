import StatusChip from '../common/StatusChip'
import {
  SHIPMENT_STATUS_LABELS,
  SHIPMENT_STATUS_COLORS,
  DISPATCH_STATUS_LABELS,
  DISPATCH_STATUS_COLORS,
  ROUTE_STATUS_LABELS,
  ROUTE_STATUS_COLORS,
} from '../../utils/statusConfig'

const STATUS_MAPS = {
  shipment: {
    labels: SHIPMENT_STATUS_LABELS,
    colors: SHIPMENT_STATUS_COLORS,
  },
  dispatch: {
    labels: DISPATCH_STATUS_LABELS,
    colors: DISPATCH_STATUS_COLORS,
  },
  route: {
    labels: ROUTE_STATUS_LABELS,
    colors: ROUTE_STATUS_COLORS,
  },
}

export default function StatusBadge({
  status,
  type = 'shipment',
  size = 'small',
}) {
  const config = STATUS_MAPS[type] || STATUS_MAPS.shipment

  return (
    <StatusChip
      status={status}
      labels={config.labels}
      colors={config.colors}
      size={size}
    />
  )
}