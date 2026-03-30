import { useQuery } from '@tanstack/react-query'
import { Autocomplete, CircularProgress, TextField } from '@mui/material'
import { apiGetDrivers, apiGetUsers } from '../../api/users'

export default function UserSelector({
  value = null,
  onChange,
  label = 'Користувач',
  params = {},
  disabled = false,
}) {
  const driversOnly = params?.role === 'driver'

  const { data, isLoading } = useQuery({
    queryKey: [driversOnly ? 'drivers' : 'users', 'selector', params],
    queryFn: () => (
      driversOnly
        ? apiGetDrivers(params)
        : apiGetUsers(params)
    ),
  })

  const options = data?.results || data || []

  return (
    <Autocomplete
      fullWidth
      options={options}
      value={value}
      onChange={(_, newValue) => onChange?.(newValue)}
      getOptionLabel={(option) => {
        const username = option?.username || ''
        const fullName =
          option?.full_name ||
          [option?.first_name, option?.last_name].filter(Boolean).join(' ')

        return fullName ? `${fullName} (${username})` : username
      }}
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
          placeholder="Оберіть водія"
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