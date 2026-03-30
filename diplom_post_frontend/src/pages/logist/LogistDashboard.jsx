import { Box, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import StatusBadge from '../../components/domain/StatusBadge'
import DataTable from '../../components/domain/DataTable'
import { useRoutes } from '../../hooks/useRoutes'
import { fDateTime } from '../../utils/formatters'

export default function LogistDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useRoutes({ page_size: 8 })

  const routes = data?.results || data || []

  const draftCount = routes.filter((r) => r.status === 'draft').length
  const confirmedCount = routes.filter((r) => r.status === 'confirmed').length
  const inProgressCount = routes.filter((r) => r.status === 'in_progress').length
  const completedCount = routes.filter((r) => r.status === 'completed').length

  const columns = [
    {
      key: 'id',
      label: 'Маршрут',
      render: (row) => row.name || row.code || `Маршрут #${row.id}`,
    },
    {
      key: 'status',
      label: 'Статус',
      render: (row) => <StatusBadge status={row.status} type="route" />,
    },
    {
      key: 'origin',
      label: 'Початок',
      render: (row) => row.origin?.name || row.origin_name || '—',
    },
    {
      key: 'destination',
      label: 'Кінець',
      render: (row) => row.destination?.name || row.destination_name || '—',
    },
    {
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
  ]

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="Логістика"
        subtitle="Маршрути, потоки та поточний стан перевезень"
        actions={
          <Button onClick={() => navigate('/logist/routes/create')}>
            Створити маршрут
          </Button>
        }
      />

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            lg: 'repeat(4, 1fr)',
          },
        }}
      >
        <StatCard title="Чернетки" value={draftCount} />
        <StatCard title="Підтверджені" value={confirmedCount} />
        <StatCard title="Виконуються" value={inProgressCount} />
        <StatCard title="Завершені" value={completedCount} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          Останні маршрути
        </Typography>

        <DataTable
          columns={columns}
          rows={routes}
          loading={false}
          onRowClick={(row) => navigate(`/logist/routes/${row.id}`)}
          emptyTitle="Маршрутів поки немає"
        />
      </Box>
    </>
  )
}