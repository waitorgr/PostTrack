import Button from '../ui/Button'
import Modal from '../ui/Modal'
import { Typography } from '@mui/material'

export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Підтвердження',
  message = 'Ви впевнені?',
  confirmText = 'Підтвердити',
  cancelText = 'Скасувати',
  confirmColor = 'error',
  loading = false,
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      actions={
        <>
          <Button variant="text" onClick={onClose} disabled={loading}>
            {cancelText}
          </Button>
          <Button color={confirmColor} onClick={onConfirm} disabled={loading}>
            {confirmText}
          </Button>
        </>
      }
    >
      <Typography variant="body1">{message}</Typography>
    </Modal>
  )
}