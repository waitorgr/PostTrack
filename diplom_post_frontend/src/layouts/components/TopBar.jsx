// src/layouts/components/TopBar.jsx

import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Typography,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import UserMenu from './UserMenu'
import { APP_NAME } from '../../utils/constants'

export default function TopBar({
  title = APP_NAME,
  onMenuClick,
  showMenuButton = true,
}) {
  return (
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {showMenuButton && (
            <IconButton
              edge="start"
              color="inherit"
              onClick={onMenuClick}
              sx={{ display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
          )}

          <Typography variant="h6" fontWeight={700}>
            {title}
          </Typography>
        </Box>

        <UserMenu />
      </Toolbar>
    </AppBar>
  )
}