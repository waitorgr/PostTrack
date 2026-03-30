import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import FilterPanel from '../../components/common/FilterPanel'
import SearchBar from '../../components/common/SearchBar'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import ShipmentTable from '../../components/domain/ShipmentTable'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { useShipments } from '../../hooks/useShipments'
import { SHIPMENT_STATUS_LABELS } from '../../utils/statusConfig'

const PAGE_SIZE = 10

export default function WarehouseParcels() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

  const statusOptions = useMemo(
    () => [
      { value: '', label: 'Усі статуси' },
      { value: 'arrived_at_facility', label: SHIPMENT_STATUS_LABELS.arrived_at_facility },
      { value: 'sorted', label: SHIPMENT_STATUS_LABELS.sorted },
      { value: 'in_transit', label: SHIPMENT_STATUS_LABELS.in_transit },
      { value: 'out_for_delivery', label: SHIPMENT_STATUS_LABELS.out_for_delivery },
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

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  return (
    <>
      <PageHeader
        title="Посилки вузла"
        subtitle="Список посилок, які зараз проходять через склад / сортування"
        actions={
          <Button onClick={() => navigate('/warehouse/sorting')}>
            Інтерфейс сортування
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
            placeholder="Пошук за трек-номером, описом..."
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
          <ShipmentTable rows={rows} loading={isLoading} />

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