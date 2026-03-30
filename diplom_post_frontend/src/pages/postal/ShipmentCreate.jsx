import { useState } from 'react'
import { Alert, Box, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import PageHeader from '../../components/common/PageHeader'
import LocationSelector from '../../components/domain/LocationSelector'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import { apiCreateShipment } from '../../api/shipments'

export default function ShipmentCreate() {
  const navigate = useNavigate()

  const [destination, setDestination] = useState(null)
  const [description, setDescription] = useState('')
  const [paymentType, setPaymentType] = useState('prepaid')
  const [weight, setWeight] = useState('')

  const [senderFirstName, setSenderFirstName] = useState('')
  const [senderLastName, setSenderLastName] = useState('')
  const [senderPatronymic, setSenderPatronymic] = useState('')
  const [senderPhone, setSenderPhone] = useState('')
  const [senderEmail, setSenderEmail] = useState('')

  const [receiverFirstName, setReceiverFirstName] = useState('')
  const [receiverLastName, setReceiverLastName] = useState('')
  const [receiverPatronymic, setReceiverPatronymic] = useState('')
  const [receiverPhone, setReceiverPhone] = useState('')
  const [receiverEmail, setReceiverEmail] = useState('')

  const [formError, setFormError] = useState('')

  const createMutation = useMutation({
    mutationFn: apiCreateShipment,
    onSuccess: (created) => {
      navigate(`/postal/shipments/${created.id}`)
    },
    onError: (error) => {
      const message =
        error.response?.data?.detail ||
        Object.values(error.response?.data || {}).flat().join(' ') ||
        'Не вдалося створити посилку'
      setFormError(message)
    },
  })

  const validateEmail = (email) => {
    if (!email) return true
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setFormError('')

    if (!destination?.id) {
      setFormError('Оберіть локацію призначення')
      return
    }

    if (!weight || Number(weight) <= 0) {
      setFormError('Вкажи коректну вагу посилки')
      return
    }

    if (!senderFirstName.trim() || !senderLastName.trim() || !senderPatronymic.trim()) {
      setFormError("Заповни повністю ПІБ відправника")
      return
    }

    if (!receiverFirstName.trim() || !receiverLastName.trim() || !receiverPatronymic.trim()) {
      setFormError("Заповни повністю ПІБ отримувача")
      return
    }

    if (!senderPhone.trim()) {
      setFormError('Вкажи телефон відправника')
      return
    }

    if (!receiverPhone.trim()) {
      setFormError('Вкажи телефон отримувача')
      return
    }

    if (!validateEmail(senderEmail)) {
      setFormError('Email відправника вказано некоректно')
      return
    }

    if (!validateEmail(receiverEmail)) {
      setFormError('Email отримувача вказано некоректно')
      return
    }

    const payload = {
      destination: destination.id,
      weight: Number(weight),
      description: description.trim() || '',
      payment_type: paymentType,

      sender_first_name: senderFirstName.trim(),
      sender_last_name: senderLastName.trim(),
      sender_patronymic: senderPatronymic.trim(),
      sender_phone: senderPhone.trim(),
      sender_email: senderEmail.trim() || '',

      receiver_first_name: receiverFirstName.trim(),
      receiver_last_name: receiverLastName.trim(),
      receiver_patronymic: receiverPatronymic.trim(),
      receiver_phone: receiverPhone.trim(),
      receiver_email: receiverEmail.trim() || '',
    }

    createMutation.mutate(payload)
  }

  return (
    <>
      <PageHeader
        title="Створення посилки"
        subtitle="Оформлення нового внутрішнього поштового відправлення"
      />

      <Card>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={3}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <Typography variant="h6" fontWeight={700}>
              Дані відправлення
            </Typography>

            <LocationSelector
              value={destination}
              onChange={setDestination}
              label="Локація призначення"
              params={{ type: 'post_office' }}
            />

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Вага"
                type="number"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                inputProps={{ min: 0, step: '0.001' }}
              />

              <Select
                label="Тип оплати"
                value={paymentType}
                onChange={(e) => setPaymentType(e.target.value)}
                options={[
                  { value: 'prepaid', label: 'Відправник сплачує' },
                  { value: 'cash_on_delivery', label: 'Отримувач сплачує' },
                ]}
              />
            </Stack>

            <Input
              label="Опис"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Необов’язково"
              multiline
              minRows={3}
            />

            <Typography variant="h6" fontWeight={700}>
              Відправник
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Прізвище"
                value={senderLastName}
                onChange={(e) => setSenderLastName(e.target.value)}
              />
              <Input
                label="Ім’я"
                value={senderFirstName}
                onChange={(e) => setSenderFirstName(e.target.value)}
              />
              <Input
                label="По батькові"
                value={senderPatronymic}
                onChange={(e) => setSenderPatronymic(e.target.value)}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Телефон"
                value={senderPhone}
                onChange={(e) => setSenderPhone(e.target.value)}
              />
              <Input
                label="Email"
                type="email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
                placeholder="Необов’язково"
              />
            </Stack>

            <Typography variant="h6" fontWeight={700}>
              Отримувач
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Прізвище"
                value={receiverLastName}
                onChange={(e) => setReceiverLastName(e.target.value)}
              />
              <Input
                label="Ім’я"
                value={receiverFirstName}
                onChange={(e) => setReceiverFirstName(e.target.value)}
              />
              <Input
                label="По батькові"
                value={receiverPatronymic}
                onChange={(e) => setReceiverPatronymic(e.target.value)}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Телефон"
                value={receiverPhone}
                onChange={(e) => setReceiverPhone(e.target.value)}
              />
              <Input
                label="Email"
                type="email"
                value={receiverEmail}
                onChange={(e) => setReceiverEmail(e.target.value)}
                placeholder="Необов’язково"
              />
            </Stack>

            <Stack direction="row" spacing={2} justifyContent="flex-end">
              <Button
                variant="text"
                onClick={() => navigate('/postal/shipments')}
                disabled={createMutation.isPending}
              >
                Скасувати
              </Button>

              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Створення...' : 'Створити посилку'}
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Card>
    </>
  )
}