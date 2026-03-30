import { Card as MuiCard, CardContent } from '@mui/material'

export default function Card({ children, sx, contentSx, ...props }) {
  return (
    <MuiCard
      sx={{
        borderRadius: 3,
        boxShadow: 1,
        ...sx,
      }}
      {...props}
    >
      <CardContent sx={contentSx}>{children}</CardContent>
    </MuiCard>
  )
}