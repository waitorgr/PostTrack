import SearchIcon from '@mui/icons-material/Search'
import { InputAdornment, TextField } from '@mui/material'

export default function SearchBar({
  value,
  onChange,
  placeholder = 'Пошук...',
  fullWidth = true,
}) {
  return (
    <TextField
      fullWidth={fullWidth}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon fontSize="small" />
          </InputAdornment>
        ),
      }}
    />
  )
}