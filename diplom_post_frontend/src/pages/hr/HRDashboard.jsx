import { Box, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import StatCard from '../../components/common/StatCard'
import Button from '../../components/ui/Button'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import { useUsers } from '../../hooks/useUsers'
import { ROLE_LABELS, WAREHOUSE_ROLES } from '../../utils/constants'

export default function HRDashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, refetch } = useUsers({ page_size: 8 })

  const users = data?.results || data || []

  const postalWorkers = users.filter((u) => u.role === 'postal_worker').length
  const warehouseWorkers = users.filter((u) => WAREHOUSE_ROLES.includes(u.role)).length
  const drivers = users.filter((u) => u.role === 'driver').length
  const logists = users.filter((u) => u.role === 'logist').length

  const columns = [
    {
      key: 'username',
      label: 'Користувач',
      render: (row) => row.username || '—',
    },
    {
      key: 'role',
      label: 'Роль',
      render: (row) => ROLE_LABELS[row.role] || row.role || '—',
    },
    {
      key: 'location',
      label: 'Локація',
      render: (row) => row.location?.name || row.location_name || '—',
    },
    {
      key: 'email',
      label: 'Email',
      render: (row) => row.email || '—',
    },
  ]

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="HR"
        subtitle="Огляд працівників системи"
        actions={
          <Button onClick={() => navigate('/hr/users/create')}>
            Створити працівника
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
        <StatCard title="Усього працівників" value={users.length} />
        <StatCard title="Працівники відділень" value={postalWorkers} />
        <StatCard title="СЦ / РЦ" value={warehouseWorkers} />
        <StatCard title="Водії + логісти" value={drivers + logists} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
          Останні працівники
        </Typography>

        <DataTable
          columns={columns}
          rows={users}
          loading={false}
          onRowClick={(row) => navigate(`/hr/users/${row.id}/edit`)}
          emptyTitle="Працівників не знайдено"
        />
      </Box>
    </>
  )
}
