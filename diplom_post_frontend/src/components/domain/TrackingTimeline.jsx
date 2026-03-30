import { Box, Divider, Stack, Typography } from '@mui/material'
import StatusBadge from './StatusBadge'
import { fDateTime } from '../../utils/formatters'
import EmptyState from '../common/EmptyState'

export default function TrackingTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <EmptyState
        title="Немає подій трекінгу"
        description="Для цієї посилки ще не зафіксовано подій."
      />
    )
  }

  return (
    <Stack divider={<Divider />} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 3 }}>
      {events.map((event, index) => (
        <Box key={event.id || index} sx={{ p: 2 }}>
          <Stack spacing={1}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
              <Typography variant="subtitle1" fontWeight={700}>
                {event.event_type_label || event.title || 'Подія'}
              </Typography>

              {event.status && <StatusBadge status={event.status} type="shipment" />}
            </Box>

            <Typography variant="body2" color="text.secondary">
              {fDateTime(event.created_at)}
            </Typography>

            {event.location?.name && (
              <Typography variant="body2">
                Локація: {event.location.name}
              </Typography>
            )}

            {event.note && (
              <Typography variant="body2">
                {event.note}
              </Typography>
            )}

            {event.created_by?.username && (
              <Typography variant="caption" color="text.secondary">
                Виконав: {event.created_by.username}
              </Typography>
            )}
          </Stack>
        </Box>
      ))}
    </Stack>
  )
}