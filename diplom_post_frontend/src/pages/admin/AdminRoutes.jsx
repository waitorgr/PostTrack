import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { useRoutes } from '../../hooks/useRoutes'
import { ROUTE_STATUS_LABELS } from '../../utils/statusConfig'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 12

export default function AdminRoutes() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

  const statusOptions = useMemo(
    () => [
      { value: '', label: 'Усі статуси' },
      ...Object.entries(ROUTE_STATUS_LABELS).map(([value, label]) => ({
        value,
        label,
      })),
    ],
    []
  )

  const queryParams = {
    page,
    page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(status ? { status } : {}),
  }

  const { data, isLoading, isError, refetch } = useRoutes(queryParams)

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const columns = [
    {
      key: 'name',
      label: 'Маршрут',
      render: (row) => row.name || row.code || `Маршрут #${row.id}`,
    },
    {
      key: 'status',
      label: 'Статус',
      render: (row) => <StatusBadge status={row.status} type="route" />,
    },
    {
      key: 'origin',
      label: 'Початок',
      render: (row) => row.origin?.name || row.origin_name || '—',
    },
    {
      key: 'destination',
      label: 'Кінець',
      render: (row) => row.destination?.name || row.destination_name || '—',
    },
    {
      key: 'driver',
      label: 'Водій',
      render: (row) =>
        row.driver?.username ||
        row.driver_name ||
        row.assigned_driver?.username ||
        '—',
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
        title="Усі маршрути"
        subtitle="Глобальний перегляд логістичних маршрутів"
        actions={
          <Button onClick={() => navigate('/logist/routes/create')}>
            Створити маршрут
          </Button>
        }
      />

      <FilterPanel>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={search}
            onChange={(value) => {
              setSearch(value)
              setPage(1)
            }}
            placeholder="Пошук за назвою або кодом маршруту..."
          />

          <Box sx={{ minWidth: { xs: '100%', md: 260 } }}>
            <Select
              label="Статус"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value)
                setPage(1)
              }}
              options={statusOptions}
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
            onRowClick={(row) => navigate(`/logist/routes/${row.id}`)}
            emptyTitle="Маршрутів не знайдено"
            emptyDescription="Спробуй змінити фільтри або пошуковий запит."
          />

          <Pagination page={page} count={totalPages} onChange={setPage} />
        </>
      )}
    </>
  )
}