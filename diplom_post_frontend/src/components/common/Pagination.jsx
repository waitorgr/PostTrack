import MuiPagination from '@mui/material/Pagination'
import { Box } from '@mui/material'

export default function Pagination({
  page = 1,
  count = 1,
  onChange,
}) {
  if (count <= 1) return null

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
      <MuiPagination page={page} count={count} onChange={(_, value) => onChange(value)} />
    </Box>
  )
}