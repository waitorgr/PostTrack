import { Box, CircularProgress } from '@mui/material'

export default function LoadingSpinner({ minHeight = 240 }) {
  return (
    <Box
      sx={{
        minHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <CircularProgress />
    </Box>
  )
}