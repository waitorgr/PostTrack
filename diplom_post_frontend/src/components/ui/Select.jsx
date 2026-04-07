import {
  FormControl,
  FormHelperText,
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
  helperText = '',
  error = false,
  required = false,
  ...props
}) {
  return (
    <FormControl fullWidth={fullWidth} size={size} error={error} required={required}>
      {label && <InputLabel>{label}</InputLabel>}
      <MuiSelect label={label} value={value} onChange={onChange} {...props}>
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </MuiSelect>
      {helperText ? <FormHelperText>{helperText}</FormHelperText> : null}
    </FormControl>
  )
}
