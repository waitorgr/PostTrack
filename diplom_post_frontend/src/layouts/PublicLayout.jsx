// src/layouts/PublicLayout.jsx

import { Box, Container } from '@mui/material'
import { Outlet } from 'react-router-dom'

export default function PublicLayout() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: 'background.default',
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Outlet />
      </Container>
    </Box>
  )
}