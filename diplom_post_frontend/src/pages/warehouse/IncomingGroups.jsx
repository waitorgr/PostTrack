import { useMemo, useState } from 'react'
import { Alert, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import FilterPanel from '../../components/common/FilterPanel'
import SearchBar from '../../components/common/SearchBar'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { apiArriveDispatch, apiGetDispatchGroups } from '../../api/dispatch'
import { DISPATCH_STATUS_LABELS } from '../../utils/statusConfig'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 10

export default function IncomingGroups() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [message, setMessage] = useState('')

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
    queryKey: ['warehouse', 'incoming-groups', { page, search, status }],
    queryFn: () =>
      apiGetDispatchGroups({
        page,
        page_size: PAGE_SIZE,
        scope: 'incoming',
        ...(search ? { search } : {}),
        ...(status ? { status } : {}),
      }),
  })

  const arriveMutation = useMutation({
    mutationFn: apiArriveDispatch,
    onSuccess: async () => {
      setMessage('Прибуття групи підтверджено. Посилки тепер доступні для ручного сортування.')
      await queryClient.invalidateQueries({ queryKey: ['warehouse'] })
      await queryClient.invalidateQueries({ queryKey: ['dispatch-groups'] })
      refetch()
    },
    onError: (error) => {
      const msg =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося підтвердити прибуття групи'
      setMessage(msg)
    },
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
      key: 'shipment_count',
      label: 'Посилок',
      render: (row) => row.shipment_count || row.shipments?.length || 0,
    },
    {
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
    {
      key: 'actions',
      label: 'Дія',
      render: (row) =>
        row.status === 'in_transit' ? (
          <Button
            size="small"
            onClick={(e) => {
              e.stopPropagation()
              setMessage('')
              arriveMutation.mutate(row.id)
            }}
            disabled={arriveMutation.isPending}
          >
            Підтвердити прибуття
          </Button>
        ) : (
          <Button
            size="small"
            variant="text"
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
        title="Вхідні групи"
        subtitle="Приймання dispatch-груп, що прибувають на поточний вузол"
      />

      {message && (
        <Alert
          severity={arriveMutation.isError ? 'error' : 'info'}
          sx={{ mb: 3 }}
        >
          {message}
        </Alert>
      )}

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
            emptyTitle="Вхідних груп не знайдено"
            emptyDescription="Спробуй змінити фільтри або пошуковий запит."
          />

          <Pagination page={page} count={totalPages} onChange={setPage} />
        </>
      )}
    </>
  )
}
