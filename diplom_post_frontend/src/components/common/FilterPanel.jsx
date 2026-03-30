import { Box, Stack } from '@mui/material'
import Card from '../ui/Card'

export default function FilterPanel({ children, actions }) {
  return (
    <Card sx={{ mb: 3 }}>
      <Stack spacing={2}>
        <Box>{children}</Box>
        {actions && <Box>{actions}</Box>}
      </Stack>
    </Card>
  )
}