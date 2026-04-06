import { useMemo, useState } from 'react'
import { Alert, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import PageHeader from '../../components/common/PageHeader'
import SearchBar from '../../components/common/SearchBar'
import Pagination from '../../components/common/Pagination'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorState from '../../components/common/ErrorState'
import StatusBadge from '../../components/domain/StatusBadge'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'

import {
  apiGetDispatchGroups,
  apiCreateDispatchGroup,
} from '../../api/dispatch'

const PAGE_SIZE = 10

export default function DispatchList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [trackingNumber, setTrackingNumber] = useState('')
  const [createError, setCreateError] = useState('')

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dispatch-groups', page, search],
    queryFn: () =>
      apiGetDispatchGroups({
        page,
        page_size: PAGE_SIZE,
        ...(search ? { search } : {}),
      }),
  })

  const rows = useMemo(() => data?.results || data || [], [data])
  const totalCount = data?.count || rows.length
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const createMutation = useMutation({
    mutationFn: async () => {
      setCreateError('')

      if (!trackingNumber.trim()) {
        throw new Error('Введіть трек-номер')
      }

      return apiCreateDispatchGroup({
        tracking_number: trackingNumber.trim(),
      })
    },
    onSuccess: async (createdGroup) => {
      setTrackingNumber('')
      await queryClient.invalidateQueries({ queryKey: ['dispatch-groups'] })
      navigate(`/postal/dispatch/${createdGroup.id}`)
    },
    onError: (error) => {
      setCreateError(
        error?.response?.data?.detail ||
          error?.response?.data?.error ||
          error.message ||
          'Помилка створення dispatch-групи'
      )
    },
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorState onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="Dispatch-групи"
        subtitle="Список сформованих груп для відправлення"
        actions={
          <Stack direction="row" spacing={2}>
            <Input
              placeholder="Трек-номер"
              value={trackingNumber}
              onChange={(e) => setTrackingNumber(e.target.value)}
            />

            <Button
              onClick={() => createMutation.mutate()}
              loading={createMutation.isPending}
              disabled={!trackingNumber.trim()}
            >
              Створити групу
            </Button>
          </Stack>
        }
      />

      {createError && <Alert severity="error">{createError}</Alert>}

      <Stack spacing={2}>
        <SearchBar
          value={search}
          onChange={(value) => {
            setSearch(value)
            setPage(1)
          }}
          placeholder="Пошук dispatch-груп"
        />

        {rows.map((group) => (
          <Card
            key={group.id}
            onClick={() => navigate(`/postal/dispatch/${group.id}`)}
            sx={{ cursor: 'pointer' }}
          >
            <Stack spacing={1.5}>
              <Typography>
                <strong>ID:</strong> {group.id}
              </Typography>

              <Typography>
                <strong>Код:</strong> {group.code || '—'}
              </Typography>

              <Typography>
                <strong>Звідки:</strong> {group.origin_name || '—'}
              </Typography>

              <Typography>
                <strong>Куди:</strong> {group.destination_name || '—'}
              </Typography>

              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Typography component="span">
                  <strong>Статус:</strong>
                </Typography>
                <StatusBadge status={group.status} type="dispatch" />
              </Stack>

              <Typography>
                <strong>К-сть посилок:</strong> {group.shipment_count ?? 0}
              </Typography>
            </Stack>
          </Card>
        ))}

        <Pagination
          page={page}
          count={totalPages}
          onChange={setPage}
        />
      </Stack>
    </>
  )
}
