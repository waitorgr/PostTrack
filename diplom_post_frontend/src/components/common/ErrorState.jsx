import { Box, Typography } from '@mui/material'
import Button from '../ui/Button'

export default function ErrorState({
  title = 'Сталася помилка',
  description = 'Не вдалося завантажити дані.',
  onRetry,
}) {
  return (
    <Box sx={{ py: 6, textAlign: 'center' }}>
      <Typography variant="h6" fontWeight={700}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        {description}
      </Typography>
      {onRetry && (
        <Box sx={{ mt: 2 }}>
          <Button onClick={onRetry}>Спробувати ще раз</Button>
        </Box>
      )}
    </Box>
  )
}