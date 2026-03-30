import { useQuery } from '@tanstack/react-query'
import { Autocomplete, CircularProgress, TextField } from '@mui/material'
import { apiGetDispatchGroups } from '../../api/dispatch'

export default function DispatchGroupSelector({
  value = null,
  onChange,
  label = 'Dispatch-група',
  params = {},
  disabled = false,
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['dispatch-groups', 'selector', params],
    queryFn: () =>
      apiGetDispatchGroups({
        page_size: 100,
        ...params,
      }),
  })

  const options = data?.results || data || []

  return (
    <Autocomplete
      fullWidth
      options={options}
      value={value}
      onChange={(_, newValue) => onChange?.(newValue)}
      getOptionLabel={(option) =>
        option?.code
          ? `${option.code} · ${option.origin_name || '—'} → ${option.destination_name || '—'}`
          : ''
      }
      isOptionEqualToValue={(option, selected) => option.id === selected?.id}
      disabled={disabled}
      loading={isLoading}
      noOptionsText="Dispatch-групи не знайдено"
      loadingText="Завантаження..."
      renderInput={(paramsInput) => (
        <TextField
          {...paramsInput}
          fullWidth
          label={label}
          placeholder="Оберіть dispatch-групу"
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