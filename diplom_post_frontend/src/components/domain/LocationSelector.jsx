import { useQuery } from '@tanstack/react-query'
import { Autocomplete, CircularProgress, TextField } from '@mui/material'
import { apiGetLocations } from '../../api/locations'

export default function LocationSelector({
  value = null,
  onChange,
  label = 'Локація',
  params = {},
  disabled = false,
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['locations', params],
    queryFn: () => apiGetLocations(params),
  })

  const options = data?.results || data || []

  return (
    <Autocomplete
      fullWidth
      options={options}
      value={value}
      onChange={(_, newValue) => onChange?.(newValue)}
      getOptionLabel={(option) =>
        option?.name || option?.full_name || option?.code || ''
      }
      isOptionEqualToValue={(option, selected) => option.id === selected?.id}
      disabled={disabled}
      loading={isLoading}
      noOptionsText="Нічого не знайдено"
      loadingText="Завантаження..."
      renderInput={(paramsInput) => (
        <TextField
          {...paramsInput}
          fullWidth
          label={label}
          placeholder="Оберіть локацію"
          InputProps={{
            ...paramsInput.InputProps,
            endAdornment: (
              <>
                {isLoading ? <CircularProgress color="inherit" size={18} /> : null}
                {paramsInput.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
    />
  )
}