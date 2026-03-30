import MuiButton from '@mui/material/Button'

export default function Button({ children, variant = 'contained', ...props }) {
  return (
    <MuiButton
      variant={variant}
      sx={{
        borderRadius: 2,
        textTransform: 'none',
        fontWeight: 600,
      }}
      {...props}
    >
      {children}
    </MuiButton>
  )
}