import { Stack, Skeleton } from '@mui/material'

export default function LoadingSkeleton({ rows = 5, height = 48 }) {
  return (
    <Stack spacing={1}>
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} variant="rounded" height={height} />
      ))}
    </Stack>
  )
}