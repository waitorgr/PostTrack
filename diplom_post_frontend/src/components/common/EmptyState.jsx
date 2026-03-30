import { Box, Typography } from '@mui/material'

export default function EmptyState({
  title = 'Немає даних',
  description,
  action,
}) {
  return (
    <Box
      sx={{
        py: 6,
        textAlign: 'center',
      }}
    >
      <Typography variant="h6" fontWeight={700}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {description}
        </Typography>
      )}
      {action && <Box sx={{ mt: 2 }}>{action}</Box>}
    </Box>
  )
}