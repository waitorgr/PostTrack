import { useState } from 'react'
import { Box } from '@mui/material'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { Toaster } from 'react-hot-toast'

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(p => !p)} />
      <Box component="main" sx={{ flex: 1, p: 3, minWidth: 0, overflow: 'auto' }}>
        <Outlet />
      </Box>
      <Toaster position="top-right" toastOptions={{ style: { fontFamily: 'Geologica, sans-serif', borderRadius: 10, fontWeight: 500 } }} />
    </Box>
  )
}
