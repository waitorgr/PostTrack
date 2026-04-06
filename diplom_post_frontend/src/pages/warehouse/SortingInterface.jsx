import { useMemo, useState } from 'react'
import { Alert, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import FilterPanel from '../../components/common/FilterPanel'
import SearchBar from '../../components/common/SearchBar'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { apiGetDispatchGroups } from '../../api/dispatch'
import { DISPATCH_STATUS_LABELS } from '../../utils/statusConfig'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 10

export default function SortingInterface() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

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
    queryKey: ['warehouse', 'outgoing-dispatch-groups', { page, search, status }],
    queryFn: () =>
      apiGetDispatchGroups({
        page,
        page_size: PAGE_SIZE,
        scope: 'outgoing',
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
      render: (row) => row.code || `Dispatch #${row.id}`,
    },
    {
      key: 'status',
      label: 'Статус',
      render: (row) => <StatusBadge status={row.status} type="dispatch" />,
    },
    {
      key: 'destination_name',
      label: 'Напрямок',
      render: (row) => row.destination_name || '—',
    },
    {
      key: 'shipment_count',
      label: 'Посилок',
      render: (row) => row.shipment_count || row.shipments_count || 0,
    },
    {
      key: 'driver_name',
      label: 'Водій',
      render: (row) => row.driver_name || 'Не призначено',
    },
    {
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
    {
      key: 'actions',
      label: 'Дія',
      render: (row) => (
        <Button
          size="small"
          onClick={(e) => {
            e.stopPropagation()
            navigate(`/warehouse/dispatch/${row.id}`)
          }}
        >
          Переглянути
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Dispatch-групи за напрямками"
        subtitle="Сформовані вихідні групи після ручного сортування посилок"
        actions={
          <Button onClick={() => navigate('/warehouse/parcels')}>
            До невідсортованих посилок
          </Button>
        }
      />

      <Alert severity="info" sx={{ mb: 3 }}>
        Нові dispatch-групи формуються автоматично під час ручного сортування посилок на сторінці «Невідсортовані посилки».
      </Alert>

      <FilterPanel>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={search}
            onChange={(value) => {
              setSearch(value)
              setPage(1)
            }}
            placeholder="Пошук за кодом групи або напрямком..."
          />

          <Select
            label="Статус"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setPage(1)
            }}
            options={statusOptions}
          />
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
            onRowClick={(row) => navigate(`/warehouse/dispatch/${row.id}`)}
            emptyTitle="Dispatch-груп не знайдено"
            emptyDescription="Після ручного сортування посилок система автоматично сформує групи за напрямками."
          />

          <Pagination
            page={page}
            count={totalPages}
            onChange={setPage}
          />
        </>
      )}
    </>
  )
}
