import { useLocation, useNavigate } from 'react-router-dom'
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  Typography, Divider, Avatar, Tooltip, IconButton,
} from '@mui/material'
import {
  DashboardRounded, LocalShippingRounded, GroupWorkRounded,
  RouteRounded, ChatRounded, AssessmentRounded, PeopleRounded,
  SearchRounded, ChevronLeftRounded, ChevronRightRounded,
  LogoutRounded, PersonRounded,
} from '@mui/icons-material'
import { useAuthStore } from '../../store/authStore'

const DRAWER_W = 240
const MINI_W   = 64

const NAV = [
  { path: '/',           label: 'Дашборд',     icon: <DashboardRounded />,      roles: ['postal_worker','warehouse_worker','logist','admin'] },
  { path: '/shipments',  label: 'Посилки',      icon: <LocalShippingRounded />,  roles: ['postal_worker','warehouse_worker','logist','admin'] },
  { path: '/dispatch',   label: 'Dispatch',     icon: <GroupWorkRounded />,      roles: ['postal_worker','warehouse_worker','admin'] },
  { path: '/routes',     label: 'Маршрути',     icon: <RouteRounded />,          roles: ['logist','driver','admin'] },
  { path: '/chat',       label: 'Чат',          icon: <ChatRounded />,           roles: ['logist','driver','admin'] },
  { path: '/reports',    label: 'Звіти',        icon: <AssessmentRounded />,     roles: ['postal_worker','warehouse_worker','logist','admin'] },
  { path: '/users',      label: 'Персонал',     icon: <PeopleRounded />,         roles: ['hr','admin'] },
  { path: '/track',      label: 'Відстеження',  icon: <SearchRounded />,         roles: ['customer'] },
  { path: '/my-shipments',label:'Мої посилки',  icon: <LocalShippingRounded />,  roles: ['customer'] },
]

export default function Sidebar({ open, onToggle }) {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const role = user?.role || ''

  const visibleNav = NAV.filter(n => n.roles.includes(role) || role === 'admin')
  const isActive = (path) => path === '/' ? pathname === '/' : pathname.startsWith(path)

  const handleLogout = async () => { await logout(); navigate('/login') }

  const content = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Logo */}
      <Box sx={{
        display: 'flex', alignItems: 'center', gap: 1.5,
        px: open ? 2.5 : 1.5, py: 2, minHeight: 64,
        borderBottom: '1px solid', borderColor: 'divider',
      }}>
        <Box sx={{
          width: 34, height: 34, borderRadius: '9px', flexShrink: 0,
          background: 'linear-gradient(135deg, #1B3F7A 0%, #2563EB 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <LocalShippingRounded sx={{ color: 'white', fontSize: 18 }} />
        </Box>
        {open && (
          <Typography variant="h6" sx={{ fontWeight: 800, color: 'primary.main', letterSpacing: '-0.02em' }}>
            PostTrack
          </Typography>
        )}
        <Box sx={{ flex: 1 }} />
        <IconButton size="small" onClick={onToggle} sx={{ color: 'text.secondary' }}>
          {open ? <ChevronLeftRounded /> : <ChevronRightRounded />}
        </IconButton>
      </Box>

      {/* Nav */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: 1, py: 1.5 }}>
        <List disablePadding>
          {visibleNav.map(({ path, label, icon }) => (
            <Tooltip key={path} title={!open ? label : ''} placement="right">
              <ListItemButton
                selected={isActive(path)}
                onClick={() => navigate(path)}
                sx={{ px: open ? 1.5 : 1, justifyContent: open ? 'flex-start' : 'center', minHeight: 42 }}
              >
                <ListItemIcon sx={{ minWidth: open ? 36 : 'unset', color: isActive(path) ? 'primary.main' : 'text.secondary' }}>
                  {icon}
                </ListItemIcon>
                {open && <ListItemText primary={label} primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: isActive(path) ? 700 : 500 }} />}
              </ListItemButton>
            </Tooltip>
          ))}
        </List>
      </Box>

      {/* User */}
      <Divider />
      <Box sx={{ px: open ? 2 : 1, py: 1.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: 13, fontWeight: 700 }}>
          {user?.first_name?.[0]}{user?.last_name?.[0]}
        </Avatar>
        {open && (
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="body2" noWrap fontWeight={600}>{user?.last_name} {user?.first_name}</Typography>
            <Typography variant="caption" color="text.secondary" noWrap>{user?.location_name || user?.role}</Typography>
          </Box>
        )}
        <Tooltip title="Вийти">
          <IconButton size="small" onClick={handleLogout} sx={{ color: 'text.secondary' }}>
            <LogoutRounded fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  )

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: open ? DRAWER_W : MINI_W,
        flexShrink: 0,
        transition: 'width .2s ease',
        '& .MuiDrawer-paper': {
          width: open ? DRAWER_W : MINI_W,
          overflowX: 'hidden',
          transition: 'width .2s ease',
          borderRight: '1px solid',
          borderColor: 'divider',
          boxSizing: 'border-box',
        },
      }}
    >
      {content}
    </Drawer>
  )
}
