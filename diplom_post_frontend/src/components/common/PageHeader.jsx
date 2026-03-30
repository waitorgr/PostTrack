import { Box, Stack, Typography } from '@mui/material'

export default function PageHeader({
  title,
  subtitle,
  action,
  actions,
  sx,
}) {
  return (
    <Box sx={{ mb: 3, ...sx }}>
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'flex-start', md: 'center' }}
        spacing={2}
      >
        <Box>
          <Typography variant="h4" fontWeight={700}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {subtitle}
            </Typography>
          )}
        </Box>

        {actions || action}
      </Stack>
    </Box>
  )
}