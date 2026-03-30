import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import ShipmentCard from '../../components/domain/ShipmentCard'
import { useShipments } from '../../hooks/useShipments'
import { SHIPMENT_STATUS_LABELS } from '../../utils/statusConfig'

const PAGE_SIZE = 8

export default function CustomerShipments() {
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
        title="Мої посилки"
        subtitle="Список усіх твоїх відправлень"
        actions={
          <Button variant="outlined" onClick={() => navigate('/track')}>
            Публічний трекінг
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
            placeholder="Пошук за трек-номером або описом..."
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
          <Box
            sx={{
              display: 'grid',
              gap: 2,
              gridTemplateColumns: {
                xs: '1fr',
                md: 'repeat(2, 1fr)',
              },
            }}
          >
            {rows.map((shipment) => (
              <ShipmentCard
                key={shipment.id}
                shipment={shipment}
                actionLabel="Деталі"
                onAction={(item) => navigate(`/customer/shipments/${item.id}`)}
              />
            ))}
          </Box>

          {!isLoading && !rows.length ? null : (
            <Pagination page={page} count={totalPages} onChange={setPage} />
          )}
        </>
      )}
    </>
  )
}