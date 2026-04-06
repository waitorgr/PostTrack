import { Box, Divider, Stack, Typography } from '@mui/material'
import StatusBadge from './StatusBadge'
import { fDateTime } from '../../utils/formatters'
import EmptyState from '../common/EmptyState'

export default function TrackingTimeline({ events = [], variant = 'default' }) {
  if (!events.length) {
    return (
      <EmptyState
        title="Немає подій трекінгу"
        description="Для цієї посилки ще не зафіксовано подій."
      />
    )
  }

  const isPublic = variant === 'public'

  return (
    <Stack
      divider={<Divider />}
      sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 3 }}
    >
      {events.map((event, index) => (
        <Box key={event.id || index} sx={{ p: 2 }}>
          <Stack spacing={0.75}>
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              gap={2}
              flexWrap="wrap"
            >
              <Typography variant="subtitle1" fontWeight={700}>
                {event.title || event.event_type_label || 'Подія'}
              </Typography>

              {!isPublic && event.status && (
                <StatusBadge status={event.status} type="shipment" />
              )}
            </Box>

            {event.created_at && (
              <Typography variant="body2" color="text.secondary">
                {fDateTime(event.created_at)}
              </Typography>
            )}

            {!isPublic && event.location?.name && (
              <Typography variant="body2">
                Локація: {event.location.name}
              </Typography>
            )}

            {!isPublic && event.note && (
              <Typography variant="body2">
                {event.note}
              </Typography>
            )}

            {!isPublic && event.created_by?.username && (
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