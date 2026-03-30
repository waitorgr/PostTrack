// src/layouts/components/UserMenu.jsx

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Avatar,
  Box,
  Button,
  Divider,
  Menu,
  MenuItem,
  Typography,
} from '@mui/material'
import { useAuthStore } from '../../store/authStore'
import { ROLE_LABELS } from '../../utils/constants'
import { useRoleRedirect } from '../../hooks/useRoleRedirect'

export default function UserMenu() {
  const navigate = useNavigate()
  const getHomeRoute = useRoleRedirect()
  const { user, logout } = useAuthStore()

  const [anchorEl, setAnchorEl] = useState(null)
  const open = Boolean(anchorEl)

  const handleOpen = (event) => setAnchorEl(event.currentTarget)
  const handleClose = () => setAnchorEl(null)

  const handleGoHome = () => {
    handleClose()
    if (user?.role) {
      navigate(getHomeRoute(user.role))
    }
  }

  const handleLogout = async () => {
    handleClose()
    await logout()
    navigate('/login', { replace: true })
  }

  const initials = user?.username?.slice(0, 1)?.toUpperCase() || 'U'

  return (
    <>
      <Button
        onClick={handleOpen}
        color="inherit"
        sx={{
          textTransform: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
        }}
      >
        <Avatar sx={{ width: 32, height: 32 }}>{initials}</Avatar>

        <Box sx={{ textAlign: 'left', display: { xs: 'none', sm: 'block' } }}>
          <Typography variant="body2" fontWeight={600}>
            {user?.username || 'Користувач'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {ROLE_LABELS[user?.role] || user?.role || '—'}
          </Typography>
        </Box>
      </Button>

      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="body2" fontWeight={600}>
            {user?.username || 'Користувач'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {ROLE_LABELS[user?.role] || user?.role || '—'}
          </Typography>
        </Box>

        <Divider />

        <MenuItem onClick={handleGoHome}>Моя головна</MenuItem>
        <MenuItem onClick={handleLogout}>Вийти</MenuItem>
      </Menu>
    </>
  )
}