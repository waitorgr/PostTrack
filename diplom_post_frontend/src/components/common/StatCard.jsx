import { Stack, Typography } from '@mui/material'
import Card from '../ui/Card'

export default function StatCard({ title, value, caption, icon, onClick }) {
  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
      }}
      onClick={onClick}
    >
      <Stack spacing={1}>
        {icon}
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" fontWeight={700}>
          {value}
        </Typography>
        {caption && (
          <Typography variant="caption" color="text.secondary">
            {caption}
          </Typography>
        )}
      </Stack>
    </Card>
  )
}