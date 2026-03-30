// src/layouts/InternalLayout.jsx

import { useState } from 'react'
import { Box } from '@mui/material'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar, { DRAWER_WIDTH } from './components/Sidebar'
import TopBar from './components/TopBar'

function getPageTitle(pathname) {
  if (pathname.includes('/postal')) return 'Робоче місце відділення'
  if (pathname.includes('/warehouse')) return 'Склад / сортування'
  if (pathname.includes('/logist')) return 'Логістика'
  if (pathname.includes('/hr')) return 'HR'
  return 'Внутрішня система'
}

export default function InternalLayout() {
  const location = useLocation()
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
          title={getPageTitle(location.pathname)}
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