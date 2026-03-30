// src/layouts/AdminLayout.jsx

import { useState } from 'react'
import { Box } from '@mui/material'
import { Outlet } from 'react-router-dom'
import Sidebar, { DRAWER_WIDTH } from './components/Sidebar'
import TopBar from './components/TopBar'

export default function AdminLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleToggleMenu = () => setMobileOpen((prev) => !prev)
  const handleCloseMenu = () => setMobileOpen(false)

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Sidebar mobileOpen={mobileOpen} onClose={handleCloseMenu} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <TopBar
          title="Адміністративна панель"
          onMenuClick={handleToggleMenu}
          showMenuButton
        />

        <Box sx={{ p: 3 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}