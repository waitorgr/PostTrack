import { useMemo, useState } from 'react'
import { Alert, Stack } from '@mui/material'
import PageHeader from '../../components/common/PageHeader'
import FilterPanel from '../../components/common/FilterPanel'
import SearchBar from '../../components/common/SearchBar'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { useShipments, useUpdateShipmentStatus } from '../../hooks/useShipments'
import { SHIPMENT_STATUS_LABELS } from '../../utils/statusConfig'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 10

export default function SortingInterface() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [message, setMessage] = useState('')
  const [pendingAction, setPendingAction] = useState(null)

  const statusOptions = useMemo(
    () => [
      { value: '', label: 'Усі статуси' },
      { value: 'arrived_at_facility', label: SHIPMENT_STATUS_LABELS.arrived_at_facility },
      { value: 'sorted', label: SHIPMENT_STATUS_LABELS.sorted },
    ],
    []
  )

  const queryParams = {
    page,
    page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(status ? { status } : {}),
  }

  const { data, isLoading, isError, refetch } = useShipments(queryParams)

  const updateStatusMutation = useUpdateShipmentStatus()

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const handleConfirmAction = async () => {
    if (!pendingAction) return

    try {
      await updateStatusMutation.mutateAsync({
        id: pendingAction.id,
        status: pendingAction.nextStatus,
        note: pendingAction.note,
      })

      setMessage(
        pendingAction.nextStatus === 'sorted'
          ? 'Посилку позначено як відсортовану'
          : 'Посилку передано на наступний етап'
      )

      setPendingAction(null)
      refetch()
    } catch (error) {
      const msg =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося оновити статус посилки'
      setMessage(msg)
      setPendingAction(null)
    }
  }

  const columns = [
    {
      key: 'tracking_number',
      label: 'Трек-номер',
      render: (row) => row.tracking_number || '—',
    },
    {
      key: 'status',
      label: 'Поточний статус',
      render: (row) => <StatusBadge status={row.status} type="shipment" />,
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
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
    {
      key: 'actions',
      label: 'Дія',
      render: (row) => {
        if (row.status === 'arrived_at_facility') {
          return (
            <Button
              size="small"
              onClick={(e) => {
                e.stopPropagation()
                setMessage('')
                setPendingAction({
                  id: row.id,
                  trackingNumber: row.tracking_number,
                  nextStatus: 'sorted',
                  note: 'Посилку відсортовано на вузлі',
                })
              }}
            >
              Позначити відсортованою
            </Button>
          )
        }

        if (row.status === 'sorted') {
          return (
            <Button
              size="small"
              color="warning"
              onClick={(e) => {
                e.stopPropagation()
                setMessage('')
                setPendingAction({
                  id: row.id,
                  trackingNumber: row.tracking_number,
                  nextStatus: 'out_for_delivery',
                  note: 'Посилку передано на наступний етап доставки',
                })
              }}
            >
              Передати далі
            </Button>
          )
        }

        return '—'
      },
    },
  ]

  return (
    <>
      <PageHeader
        title="Інтерфейс сортування"
        subtitle="Швидка обробка посилок на вузлі"
      />

      {message && (
        <Alert
          severity={updateStatusMutation.isError ? 'error' : 'info'}
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
            placeholder="Пошук за трек-номером..."
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
            emptyTitle="Посилок для сортування не знайдено"
            emptyDescription="Спробуй змінити фільтри або пошуковий запит."
          />

          <Pagination
            page={page}
            count={totalPages}
            onChange={setPage}
          />
        </>
      )}

      <ConfirmDialog
        open={Boolean(pendingAction)}
        onClose={() => setPendingAction(null)}
        onConfirm={handleConfirmAction}
        title="Підтвердження дії"
        message={
          pendingAction?.nextStatus === 'sorted'
            ? `Позначити посилку ${pendingAction?.trackingNumber || ''} як відсортовану?`
            : `Передати посилку ${pendingAction?.trackingNumber || ''} на наступний етап?`
        }
        confirmText={
          pendingAction?.nextStatus === 'sorted'
            ? 'Позначити відсортованою'
            : 'Передати далі'
        }
        loading={updateStatusMutation.isPending}
      />
    </>
  )
}