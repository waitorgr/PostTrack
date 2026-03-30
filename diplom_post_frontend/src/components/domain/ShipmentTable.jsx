import { Typography } from '@mui/material'
import { fDateTime } from '../../utils/formatters'
import DataTable from './DataTable'
import StatusBadge from './StatusBadge'

export default function ShipmentTable({
  rows = [],
  loading = false,
  onRowClick,
}) {
  const columns = [
    {
      key: 'tracking_number',
      label: 'Трек-номер',
      render: (row) => (
        <Typography fontWeight={600}>
          {row.tracking_number || '—'}
        </Typography>
      ),
    },
    {
      key: 'origin',
      label: 'Звідки',
      render: (row) => row.origin?.name || row.origin_name || '—',
    },
    {
      key: 'destination',
      label: 'Куди',
      render: (row) => row.destination?.name || row.destination_name || '—',
    },
    {
      key: 'status',
      label: 'Статус',
      render: (row) => <StatusBadge status={row.status} type="shipment" />,
    },
    {
      key: 'created_at',
      label: 'Створено',
      render: (row) => fDateTime(row.created_at),
    },
  ]

  return (
    <DataTable
      columns={columns}
      rows={rows}
      loading={loading}
      onRowClick={onRowClick}
      emptyTitle="Посилки не знайдено"
      emptyDescription="Спробуй змінити фільтри або пошуковий запит."
      getRowKey={(row) => row.id || row.tracking_number}
    />
  )
}