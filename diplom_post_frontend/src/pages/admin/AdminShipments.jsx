import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import ShipmentTable from '../../components/domain/ShipmentTable'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { useShipments } from '../../hooks/useShipments'
import { SHIPMENT_STATUS_LABELS } from '../../utils/statusConfig'

const PAGE_SIZE = 12

export default function AdminShipments() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

  const statusOptions = useMemo(
    () => [
      { value: '', label: 'Усі статуси' },
      ...Object.entries(SHIPMENT_STATUS_LABELS).map(([value, label]) => ({
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

  const { data, isLoading, isError, refetch } = useShipments(queryParams)

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  return (
    <>
      <PageHeader
        title="Усі посилки"
        subtitle="Глобальний перегляд усіх поштових відправлень у системі"
        actions={
          <Button onClick={() => navigate('/postal/shipments/create')}>
            Створити посилку
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
          <ShipmentTable
            rows={rows}
            loading={isLoading}
            onRowClick={(row) => navigate(`/postal/shipments/${row.id}`)}
          />

          <Pagination page={page} count={totalPages} onChange={setPage} />
        </>
      )}
    </>
  )
}