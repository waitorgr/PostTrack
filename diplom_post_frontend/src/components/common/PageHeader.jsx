import { Box, Typography, Breadcrumbs, Link } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function PageHeader({ title, subtitle, breadcrumbs = [], action }) {
  const navigate = useNavigate()
  return (
    <Box sx={{ mb: 3 }}>
      {breadcrumbs.length > 0 && (
        <Breadcrumbs sx={{ mb: 1 }}>
          {breadcrumbs.map((b, i) =>
            i < breadcrumbs.length - 1 ? (
              <Link key={b.label} underline="hover" sx={{ cursor: 'pointer', fontSize: 13, color: 'text.secondary' }}
                onClick={() => navigate(b.path)}>{b.label}</Link>
            ) : (
              <Typography key={b.label} sx={{ fontSize: 13, color: 'text.primary', fontWeight: 600 }}>{b.label}</Typography>
            )
          )}
        </Breadcrumbs>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 800, color: 'text.primary' }}>{title}</Typography>
          {subtitle && <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>{subtitle}</Typography>}
        </Box>
        {action && <Box>{action}</Box>}
      </Box>
    </Box>
  )
}
