import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Select from '../../components/ui/Select'
import { apiGetDispatchGroups } from '../../api/dispatch'
import { DISPATCH_STATUS_LABELS } from '../../utils/statusConfig'
import { fDateTime } from '../../utils/formatters'
import { useNavigate } from 'react-router-dom'

const PAGE_SIZE = 10

export default function DispatchOverview() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const navigate = useNavigate()

  const statusOptions = useMemo(
    () => [
      { value: '', label: 'Усі статуси' },
      ...Object.entries(DISPATCH_STATUS_LABELS).map(([value, label]) => ({
        value,
        label,
      })),
    ],
    []
  )

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['logist', 'dispatch-overview', { page, search, status }],
    queryFn: () =>
      apiGetDispatchGroups({
        page,
        page_size: PAGE_SIZE,
        ...(search ? { search } : {}),
        ...(status ? { status } : {}),
      }),
  })

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const columns = [
    {
      key: 'code',
      label: 'Група',
      render: (row) => row.code || row.name || `Dispatch #${row.id}`,
    },
    {
      key: 'status',
      label: 'Статус',
      render: (row) => <StatusBadge status={row.status} type="dispatch" />,
    },
    {
      key: 'origin',
      label: 'Звідки',
      render: (row) => row.origin?.name || row.origin_name || '—',
    },
    {
      key: 'destination',
      label: 'Куди',
      render: (row) => row.destination?.name || row.destination_name || '—',
    },
    {
      key: 'shipments_count',
      label: 'Посилок',
      render: (row) => row.shipments_count || row.shipments?.length || 0,
    },
    {
      key: 'route',
      label: 'Маршрут',
      render: (row) =>
        row.route?.name ||
        row.route_name ||
        row.trip?.name ||
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
        title="Dispatch overview"
        subtitle="Огляд dispatch-груп у логістичному ланцюгу"
      />

      <FilterPanel>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={search}
            onChange={(value) => {
              setSearch(value)
              setPage(1)
            }}
            placeholder="Пошук за кодом групи..."
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
            onRowClick={(row) => navigate(`/logist/dispatches/${row.id}`)}
            emptyTitle="Dispatch-групи не знайдено"
            emptyDescription="Спробуй змінити фільтри або пошуковий запит."
          />

          <Pagination page={page} count={totalPages} onChange={setPage} />
        </>
      )}
    </>
  )
}