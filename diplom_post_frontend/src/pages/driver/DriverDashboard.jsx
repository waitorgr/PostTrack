import { Box, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import StatusBadge from '../../components/domain/StatusBadge'
import { useRoutes } from '../../hooks/useRoutes'
import { fDateTime } from '../../utils/formatters'

export default function DriverDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useRoutes({ page_size: 6 })

  const routes = data?.results || data || []

  const activeRoute = routes.find((r) => r.status === 'in_progress') || null
  const assignedCount = routes.length
  const confirmedCount = routes.filter((r) => r.status === 'confirmed').length
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
      key: 'destination',
      label: 'Кінцева точка',
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
        title="Кабінет водія"
        subtitle="Твої активні та призначені маршрути"
        actions={
          activeRoute ? (
            <Button onClick={() => navigate(`/driver/routes/${activeRoute.id}`)}>
              Відкрити активний маршрут
            </Button>
          ) : null
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
        <StatCard title="Усього маршрутів" value={assignedCount} />
        <StatCard title="Підтверджені" value={confirmedCount} />
        <StatCard title="Активний маршрут" value={activeRoute ? 1 : 0} />
        <StatCard title="Завершені" value={completedCount} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          Мої маршрути
        </Typography>

        <DataTable
          columns={columns}
          rows={routes}
          loading={false}
          onRowClick={(row) => navigate(`/driver/routes/${row.id}`)}
          emptyTitle="Маршрутів поки немає"
        />
      </Box>
    </>
  )
}