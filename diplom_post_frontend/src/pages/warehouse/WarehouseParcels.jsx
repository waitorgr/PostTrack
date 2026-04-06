import { useState } from 'react'
import { Alert, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import FilterPanel from '../../components/common/FilterPanel'
import SearchBar from '../../components/common/SearchBar'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import DataTable from '../../components/domain/DataTable'
import Button from '../../components/ui/Button'
import { useManualSortShipment, useShipments } from '../../hooks/useShipments'
import { fDateTime } from '../../utils/formatters'

const PAGE_SIZE = 10

export default function WarehouseParcels() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [message, setMessage] = useState('')
  const [messageSeverity, setMessageSeverity] = useState('info')
  const [pendingShipment, setPendingShipment] = useState(null)

  const queryParams = {
    page,
    page_size: PAGE_SIZE,
    status: 'arrived_at_facility',
    ...(search ? { search } : {}),
  }

  const { data, isLoading, isError, refetch } = useShipments(queryParams)
  const manualSortMutation = useManualSortShipment()

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const handleConfirmSort = async () => {
    if (!pendingShipment) return

    try {
      const result = await manualSortMutation.mutateAsync(pendingShipment.id)
      const nextHopName = result?.next_hop?.name || pendingShipment.next_hop_name || 'наступного вузла'
      const groupCode = result?.dispatch_group?.code || '—'

      setMessage(
        `Посилку ${pendingShipment.tracking_number} відсортовано. Наступний етап: ${nextHopName}. Dispatch-група: ${groupCode}.`
      )
      setMessageSeverity('success')
      setPendingShipment(null)
      refetch()
    } catch (error) {
      const msg =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося виконати ручне сортування посилки.'

      setMessage(msg)
      setMessageSeverity('error')
      setPendingShipment(null)
    }
  }

  const columns = [
    {
      key: 'tracking_number',
      label: 'Трек-номер',
      render: (row) => row.tracking_number || '—',
    },
    {
      key: 'receiver_full_name',
      label: 'Отримувач',
      render: (row) => row.receiver_full_name || '—',
    },
    {
      key: 'destination_name',
      label: 'Кінцеве відділення',
      render: (row) => row.destination_name || '—',
    },
    {
      key: 'next_hop_name',
      label: 'Наступний етап',
      render: (row) => row.next_hop_name || 'Не визначено',
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
            setMessage('')
            setPendingShipment(row)
          }}
        >
          Ручне сортування
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Невідсортовані посилки"
        subtitle="Черга посилок, що прибули на вузол і очікують ручного сортування"
        actions={
          <Button onClick={() => navigate('/warehouse/sorting')}>
            Перейти до dispatch-груп
          </Button>
        }
      />

      {message ? (
        <Alert severity={messageSeverity} sx={{ mb: 3 }}>
          {message}
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
            placeholder="Пошук за трек-номером, ПІБ чи телефоном..."
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
            emptyTitle="Невідсортованих посилок немає"
            emptyDescription="Після підтвердження прибуття груп посилки з'являться тут для ручного сортування."
          />

          <Pagination
            page={page}
            count={totalPages}
            onChange={setPage}
          />
        </>
      )}

      <ConfirmDialog
        open={Boolean(pendingShipment)}
        onClose={() => setPendingShipment(null)}
        onConfirm={handleConfirmSort}
        title="Підтвердження ручного сортування"
        message={
          pendingShipment
            ? `Посилка ${pendingShipment.tracking_number} буде направлена до ${pendingShipment.next_hop_name || 'наступного вузла'}. Підтвердити сортування?`
            : ''
        }
        confirmText="Підтвердити сортування"
        loading={manualSortMutation.isPending}
      />
    </>
  )
}
