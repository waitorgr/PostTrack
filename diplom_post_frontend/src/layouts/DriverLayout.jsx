// src/layouts/DriverLayout.jsx

import { useMemo } from 'react'
import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
  Box,
  Paper,
  Toolbar,
  Typography,
} from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import RouteIcon from '@mui/icons-material/Route'
import PersonIcon from '@mui/icons-material/Person'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import UserMenu from './components/UserMenu'

export default function DriverLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  const value = useMemo(() => {
    if (location.pathname.startsWith('/driver/routes')) return '/driver/routes'
    return '/driver/dashboard'
  }, [location.pathname])

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default', pb: 8 }}>
      <AppBar
        position="sticky"
        color="inherit"
        elevation={0}
        sx={{
          borderBottom: '1px solid',
          borderColor: 'divider',
          backgroundColor: 'background.paper',
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="h6" fontWeight={700}>
            Кабінет водія
          </Typography>
          <UserMenu />
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2 }}>
        <Outlet />
      </Box>

      <Paper
        elevation={8}
        sx={{
          position: 'fixed',
          left: 0,
          right: 0,
          bottom: 0,
          borderTop: '1px solid',
          borderColor: 'divider',
        }}
      >
        <BottomNavigation
          showLabels
          value={value}
          onChange={(_, newValue) => navigate(newValue)}
        >
          <BottomNavigationAction
            label="Головна"
            value="/driver/dashboard"
            icon={<DashboardIcon />}
          />
          <BottomNavigationAction
            label="Маршрути"
            value="/driver/routes"
            icon={<RouteIcon />}
          />
          <BottomNavigationAction
            label="Профіль"
            value="/driver/dashboard"
            icon={<PersonIcon />}
          />
        </BottomNavigation>
      </Paper>
    </Box>
  )
}