import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary:   { main: '#1B3F7A', light: '#2563EB', dark: '#112952', contrastText: '#fff' },
    secondary: { main: '#0EA5E9', light: '#38BDF8', dark: '#0284C7', contrastText: '#fff' },
    success:   { main: '#16A34A', light: '#22C55E', dark: '#15803D' },
    warning:   { main: '#D97706', light: '#F59E0B', dark: '#B45309' },
    error:     { main: '#DC2626', light: '#EF4444', dark: '#B91C1C' },
    background: { default: '#F0F4FA', paper: '#FFFFFF' },
    text: { primary: '#0F172A', secondary: '#475569' },
    divider: '#E2E8F0',
  },
  typography: {
    fontFamily: '"Geologica", sans-serif',
    h1: { fontWeight: 800, letterSpacing: '-0.03em' },
    h2: { fontWeight: 700, letterSpacing: '-0.02em' },
    h3: { fontWeight: 700, letterSpacing: '-0.02em' },
    h4: { fontWeight: 700, letterSpacing: '-0.01em' },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
    button: { fontWeight: 600, letterSpacing: '0.01em' },
    overline: { fontWeight: 600, letterSpacing: '0.1em' },
    mono: { fontFamily: '"JetBrains Mono", monospace', fontWeight: 500 },
  },
  shape: { borderRadius: 10 },
  shadows: [
    'none',
    '0 1px 3px rgba(15,23,42,.06), 0 1px 2px rgba(15,23,42,.04)',
    '0 4px 6px -1px rgba(15,23,42,.07), 0 2px 4px -2px rgba(15,23,42,.05)',
    '0 10px 15px -3px rgba(15,23,42,.08), 0 4px 6px -4px rgba(15,23,42,.05)',
    '0 20px 25px -5px rgba(15,23,42,.10), 0 8px 10px -6px rgba(15,23,42,.06)',
    ...Array(20).fill('none'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 8, textTransform: 'none', fontWeight: 600, padding: '8px 18px' },
        containedPrimary: {
          background: 'linear-gradient(135deg, #1B3F7A 0%, #2563EB 100%)',
          boxShadow: '0 2px 8px rgba(37,99,235,.35)',
          '&:hover': { background: 'linear-gradient(135deg, #112952 0%, #1D4ED8 100%)' },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 3px rgba(15,23,42,.06)',
        },
      },
    },
    MuiChip: {
      styleOverrides: { root: { fontWeight: 600, borderRadius: 6 } },
    },
    MuiTextField: {
      defaultProps: { size: 'small', variant: 'outlined' },
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: '#F8FAFC',
            '&:hover fieldset': { borderColor: '#2563EB' },
            '&.Mui-focused fieldset': { borderColor: '#1B3F7A' },
          },
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#F0F4FA',
            fontWeight: 700,
            color: '#1B3F7A',
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: '#F8FAFC' },
          '&:last-child td': { borderBottom: 0 },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginBottom: 2,
          '&.Mui-selected': {
            backgroundColor: '#EFF6FF',
            color: '#1B3F7A',
            '& .MuiListItemIcon-root': { color: '#1B3F7A' },
            '&:hover': { backgroundColor: '#DBEAFE' },
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: { borderRadius: 99, height: 6, backgroundColor: '#E2E8F0' },
        bar: { borderRadius: 99 },
      },
    },
  },
})
