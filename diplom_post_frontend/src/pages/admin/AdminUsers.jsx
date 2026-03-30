import { useMemo, useState } from 'react'
import { Box, Stack } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import FilterPanel from '../../components/common/FilterPanel'
import Pagination from '../../components/common/Pagination'
import ErrorState from '../../components/common/ErrorState'
import DataTable from '../../components/domain/DataTable'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import { useUsers } from '../../hooks/useUsers'
import { ROLE_LABELS, WORKER_ROLES } from '../../utils/constants'

const PAGE_SIZE = 12

export default function AdminUsers() {
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [role, setRole] = useState('')
  const [page, setPage] = useState(1)

  const roleOptions = useMemo(
    () => [
      { value: '', label: 'Усі ролі' },
      ...WORKER_ROLES.map((value) => ({
        value,
        label: ROLE_LABELS[value] || value,
      })),
      { value: 'customer', label: ROLE_LABELS.customer },
      { value: 'admin', label: ROLE_LABELS.admin },
    ],
    []
  )

  const queryParams = {
    page,
    page_size: PAGE_SIZE,
    ...(search ? { search } : {}),
    ...(role ? { role } : {}),
  }

  const { data, isLoading, isError, refetch } = useUsers(queryParams)

  const rows = data?.results || data || []
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const columns = [
    {
      key: 'username',
      label: 'Користувач',
      render: (row) => row.username || '—',
    },
    {
      key: 'full_name',
      label: "Ім'я",
      render: (row) =>
        [row.first_name, row.last_name].filter(Boolean).join(' ') || '—',
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

  return (
    <>
      <PageHeader
        title="Усі користувачі"
        subtitle="Глобальний перегляд працівників і користувачів системи"
        actions={
          <Button onClick={() => navigate('/hr/users/create')}>
            Створити користувача
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
            placeholder="Пошук за логіном, email, ім’ям..."
          />

          <Box sx={{ minWidth: { xs: '100%', md: 260 } }}>
            <Select
              label="Роль"
              value={role}
              onChange={(e) => {
                setRole(e.target.value)
                setPage(1)
              }}
              options={roleOptions}
            />
          </Box>
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
            onRowClick={(row) => navigate(`/hr/users/${row.id}/edit`)}
            emptyTitle="Користувачів не знайдено"
            emptyDescription="Спробуй змінити фільтри або пошуковий запит."
          />

          <Pagination page={page} count={totalPages} onChange={setPage} />
        </>
      )}
    </>
  )
}