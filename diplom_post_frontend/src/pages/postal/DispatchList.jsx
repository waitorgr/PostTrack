import { useMemo, useState } from 'react'
import { Alert, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { apiCreateDispatchGroup, apiGetDispatchGroups } from '../../api/dispatch'
import { apiMe } from '../../api/auth'
import { apiGetLocations } from '../../api/locations'
import { DISPATCH_STATUS_LABELS } from '../../utils/statusConfig'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 10

function extractApiError(error) {
  const data = error?.response?.data

  if (!data) return 'Не вдалося створити dispatch-групу.'

  if (typeof data.detail === 'string') return data.detail

  if (typeof data === 'object') {
    const firstEntry = Object.entries(data)[0]
    if (firstEntry) {
      const [, value] = firstEntry
      if (Array.isArray(value)) return value[0]
      if (typeof value === 'string') return value
    }
  }

  return 'Не вдалося створити dispatch-групу.'
}

function getNextDestinationId(me, locations) {
  if (!me?.location) {
    throw new Error('У користувача немає прив’язаної локації.')
  }

  if (!Array.isArray(locations) || locations.length === 0) {
    throw new Error('Не вдалося завантажити список локацій.')
  }

  const currentLocation = locations.find((loc) => loc.id === me.location)

  if (!currentLocation) {
    throw new Error('Не знайдено поточну локацію користувача.')
  }

  let targetCode = null

  if (currentLocation.type === 'post_office') {
    targetCode = currentLocation.code.slice(0, 5)
  } else if (currentLocation.type === 'distribution_center') {
    targetCode = currentLocation.code.slice(0, 2)
  } else if (currentLocation.type === 'sorting_center') {
    throw new Error('Для сортувального центру destination треба визначати окремо.')
  } else {
    throw new Error('Невідомий тип локації користувача.')
  }

  const destination = locations.find((loc) => loc.code === targetCode)

  if (!destination) {
    throw new Error(`Не знайдено destination для коду ${targetCode}.`)
  }

  return destination.id
}

export default function DispatchList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [createError, setCreateError] = useState('')

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
    queryKey: ['dispatch-groups', { page, search, status }],
    queryFn: () =>
      apiGetDispatchGroups({
        page,
        page_size: PAGE_SIZE,
        ...(search ? { search } : {}),
        ...(status ? { status } : {}),
      }),
  })

  const { data: me, isLoading: isMeLoading } = useQuery({
    queryKey: ['me'],
    queryFn: apiMe,
  })

  const { data: locations = [], isLoading: areLocationsLoading } = useQuery({
    queryKey: ['locations-for-dispatch'],
    queryFn: () => apiGetLocations(),
  })

  const destinationId = useMemo(() => {
    try {
      if (!me || !locations.length) return null
      return getNextDestinationId(me, locations)
    } catch {
      return null
    }
  }, [me, locations])

  const createMutation = useMutation({
    mutationFn: async () => {
      setCreateError('')

      const resolvedDestinationId = getNextDestinationId(me, locations)

      return apiCreateDispatchGroup({
        destination: resolvedDestinationId,
      })
    },
    onSuccess: (createdGroup) => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-groups'] })
      navigate(`/postal/dispatch/${createdGroup.id}`)
    },
    onError: (error) => {
      if (error instanceof Error && !error.response) {
        setCreateError(error.message)
        return
      }

      setCreateError(extractApiError(error))
    },
  })

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const columns = [
    {
      key: 'id',
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
      label: 'Походження',
      render: (row) => row.origin?.name || row.origin_name || '—',
    },
    {
      key: 'destination',
      label: 'Призначення',
      render: (row) => row.destination?.name || row.destination_name || '—',
    },
    {
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
  ]

  const createDisabled =
    createMutation.isPending ||
    isMeLoading ||
    areLocationsLoading ||
    !destinationId

  return (
    <>
      <PageHeader
        title="Dispatch-групи"
        subtitle="Список сформованих груп для відправлення"
        actions={
          <Button
            onClick={() => createMutation.mutate()}
            loading={createMutation.isPending}
            disabled={createDisabled}
          >
            Створити групу
          </Button>
        }
      />

      {createError ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {createError}
        </Alert>
      ) : null}

      {!destinationId && !isMeLoading && !areLocationsLoading ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Не вдалося автоматично визначити destination для поточної локації.
        </Alert>
      ) : null}

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
            onRowClick={(row) => navigate(`/postal/dispatch/${row.id}`)}
            emptyTitle="Dispatch-групи не знайдено"
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