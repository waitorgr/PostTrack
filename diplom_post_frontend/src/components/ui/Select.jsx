import {
  FormControl,
  InputLabel,
  MenuItem,
  Select as MuiSelect,
} from '@mui/material'

export default function Select({
  label,
  value,
  onChange,
  options = [],
  fullWidth = true,
  size = 'medium',
  ...props
}) {
  return (
    <FormControl fullWidth={fullWidth} size={size}>
      {label && <InputLabel>{label}</InputLabel>}
      <MuiSelect label={label} value={value} onChange={onChange} {...props}>
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </MuiSelect>
    </FormControl>
  )
}