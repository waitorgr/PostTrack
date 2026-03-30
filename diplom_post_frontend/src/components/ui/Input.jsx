import TextField from '@mui/material/TextField'

export default function Input({
  fullWidth = true,
  size = 'medium',
  ...props
}) {
  return <TextField fullWidth={fullWidth} size={size} {...props} />
}