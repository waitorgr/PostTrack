import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import ErrorState from '../../components/common/ErrorState'
import ShipmentTable from '../../components/domain/ShipmentTable'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { useShipments } from '../../hooks/useShipments'
import { SHIPMENT_STATUS_LABELS } from '../../utils/statusConfig'

export default function ShipmentList() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')

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
    page_size: 1000,
    ...(search ? { search } : {}),
    ...(status ? { status } : {}),
  }

  const { data, isLoading, isError, refetch } = useShipments(queryParams)

  const rows = data?.results || data || []

  return (
    <>
      <PageHeader
        title="Посилки"
        subtitle="Пошук, фільтрація та перегляд усіх посилок"
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
            onChange={setSearch}
            placeholder="Пошук за трек-номером, описом..."
          />

          <Box sx={{ minWidth: { xs: '100%', md: 260 } }}>
            <Select
              label="Статус"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              options={statusOptions}
            />
          </Box>
        </Stack>
      </FilterPanel>

      {isError ? (
        <ErrorState onRetry={refetch} />
      ) : (
        <ShipmentTable
          rows={rows}
          loading={isLoading}
          onRowClick={(row) => navigate(`/postal/shipments/${row.id}`)}
        />
      )}
    </>
  )
}