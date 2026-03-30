import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import Select from '../../components/ui/Select'
import { apiGetLocations } from '../../api/locations'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 10

const LOCATION_TYPE_OPTIONS = [
  { value: '', label: 'Усі типи' },
  { value: 'POST_OFFICE', label: 'Поштове відділення' },
  { value: 'SORTING_CENTER', label: 'Сортувальний центр' },
  { value: 'DISTRIBUTION_CENTER', label: 'Розподільчий центр' },
]

export default function LocationsList() {
  const [search, setSearch] = useState('')
  const [locationType, setLocationType] = useState('')
  const [page, setPage] = useState(1)

  const queryParams = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      ...(search ? { search } : {}),
      ...(locationType ? { location_type: locationType } : {}),
    }),
    [page, search, locationType]
  )

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['hr', 'locations', queryParams],
    queryFn: () => apiGetLocations(queryParams),
  })

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const columns = [
    {
      key: 'name',
      label: 'Назва',
      render: (row) => row.name || '—',
    },
    {
      key: 'code',
      label: 'Код',
      render: (row) => row.code || '—',
    },
    {
      key: 'location_type',
      label: 'Тип',
      render: (row) => row.location_type_display || row.location_type || '—',
    },
    {
      key: 'city',
      label: 'Місто',
      render: (row) => row.city?.name || row.city_name || '—',
    },
    {
      key: 'region',
      label: 'Регіон',
      render: (row) => row.region?.name || row.region_name || row.city?.region?.name || '—',
    },
    {
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
  ]

  return (
    <>
      <PageHeader
        title="Локації"
        subtitle="Довідник локацій для прив’язки працівників"
      />

      <FilterPanel>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={search}
            onChange={(value) => {
              setSearch(value)
              setPage(1)
            }}
            placeholder="Пошук за назвою або кодом..."
          />

          <Box sx={{ minWidth: { xs: '100%', md: 260 } }}>
            <Select
              label="Тип локації"
              value={locationType}
              onChange={(e) => {
                setLocationType(e.target.value)
                setPage(1)
              }}
              options={LOCATION_TYPE_OPTIONS}
            />
          </Box>
        </Stack>
      </FilterPanel>

      {isError ? (
        <ErrorState onRetry={refetch} />
      ) : (
        <>
          <DataTable
            columns={columns}
            rows={rows}
            loading={isLoading}
            emptyTitle="Локації не знайдено"
            emptyDescription="Спробуй змінити фільтри або пошуковий запит."
          />

          <Pagination page={page} count={totalPages} onChange={setPage} />
        </>
      )}
    </>
  )
}