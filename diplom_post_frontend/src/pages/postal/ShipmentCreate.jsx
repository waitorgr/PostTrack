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
import { apiDownloadShipmentReceipt } from '../../api/reports'
import {
  mapApiErrorsToForm,
  validateDestination,
  validateEmail,
  validateFullNamePart,
  validatePhone,
  validateWeight,
} from '../../utils/validators'

const initialForm = {
  destination: null,
  description: '',
  payment_type: 'prepaid',
  weight: '',

  sender_first_name: '',
  sender_last_name: '',
  sender_patronymic: '',
  sender_phone: '',
  sender_email: '',

  receiver_first_name: '',
  receiver_last_name: '',
  receiver_patronymic: '',
  receiver_phone: '',
  receiver_email: '',
}

const fieldNames = Object.keys(initialForm)

function getFieldHint(field) {
  const hints = {
    destination: 'Оберіть поштове відділення, куди потрібно доставити посилку',
    weight: 'Вкажіть вагу в кілограмах, наприклад 1.25',
    payment_type: 'Хто сплачує доставку',
    description: 'Необов’язково. Можна коротко описати вміст посилки',
    sender_last_name: 'Обов’язкове поле',
    sender_first_name: 'Обов’язкове поле',
    sender_patronymic: 'Обов’язкове поле',
    sender_phone: 'Формат: +380501234567 або 0501234567',
    sender_email: 'Необов’язково. Наприклад: sender@example.com',
    receiver_last_name: 'Обов’язкове поле',
    receiver_first_name: 'Обов’язкове поле',
    receiver_patronymic: 'Обов’язкове поле',
    receiver_phone: 'Формат: +380501234567 або 0501234567',
    receiver_email: 'Необов’язково. Наприклад: receiver@example.com',
  }

  return hints[field] || ''
}

function validateForm(values) {
  return {
    destination: validateDestination(values.destination),
    weight: validateWeight(values.weight),
    sender_last_name: validateFullNamePart(values.sender_last_name, 'Прізвище відправника'),
    sender_first_name: validateFullNamePart(values.sender_first_name, 'Ім’я відправника'),
    sender_patronymic: validateFullNamePart(values.sender_patronymic, 'По батькові відправника'),
    sender_phone: validatePhone(values.sender_phone, 'Телефон відправника'),
    sender_email: validateEmail(values.sender_email, 'Email відправника'),
    receiver_last_name: validateFullNamePart(values.receiver_last_name, 'Прізвище отримувача'),
    receiver_first_name: validateFullNamePart(values.receiver_first_name, 'Ім’я отримувача'),
    receiver_patronymic: validateFullNamePart(values.receiver_patronymic, 'По батькові отримувача'),
    receiver_phone: validatePhone(values.receiver_phone, 'Телефон отримувача'),
    receiver_email: validateEmail(values.receiver_email, 'Email отримувача'),
  }
}

function hasErrors(errors) {
  return Object.values(errors).some(Boolean)
}

export default function ShipmentCreate() {
  const navigate = useNavigate()

  const [form, setForm] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})
  const [formError, setFormError] = useState('')

  const createMutation = useMutation({
    mutationFn: apiCreateShipment,
    onSuccess: async (created) => {
      try {
        await apiDownloadShipmentReceipt(created.id)
      } catch (error) {
        console.error('Не вдалося автоматично завантажити квитанцію', error)
      }

      navigate(`/postal/shipments/${created.id}`)
    },
    onError: (error) => {
      const responseData = error.response?.data
      const { fieldErrors, generalError } = mapApiErrorsToForm(responseData, fieldNames)

      if (Object.keys(fieldErrors).length) {
        setErrors((prev) => ({ ...prev, ...fieldErrors }))
        setTouched((prev) => ({
          ...prev,
          ...Object.fromEntries(Object.keys(fieldErrors).map((key) => [key, true])),
        }))
      }

      setFormError(generalError || 'Не вдалося створити посилку')
    },
  })

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setFormError('')

    if (touched[field]) {
      const nextValues = { ...form, [field]: value }
      setErrors((prev) => ({
        ...prev,
        [field]: validateForm(nextValues)[field] || '',
      }))
    }
  }

  const touchField = (field) => {
    setTouched((prev) => ({ ...prev, [field]: true }))
    setErrors((prev) => ({
      ...prev,
      [field]: validateForm(form)[field] || '',
    }))
  }

  const getFieldError = (field) => Boolean(touched[field] && errors[field])
  const getFieldHelper = (field) =>
    touched[field] && errors[field] ? errors[field] : getFieldHint(field)

  const handleSubmit = (e) => {
    e.preventDefault()
    setFormError('')

    const validationErrors = validateForm(form)
    setErrors(validationErrors)
    setTouched(Object.fromEntries(fieldNames.map((field) => [field, true])))

    if (hasErrors(validationErrors)) {
      setFormError('Перевірте форму та виправте поля з помилками')
      return
    }

    const payload = {
      destination: form.destination.id,
      weight: Number(form.weight),
      description: form.description.trim(),
      payment_type: form.payment_type,

      sender_first_name: form.sender_first_name.trim(),
      sender_last_name: form.sender_last_name.trim(),
      sender_patronymic: form.sender_patronymic.trim(),
      sender_phone: form.sender_phone.trim(),
      sender_email: form.sender_email.trim(),

      receiver_first_name: form.receiver_first_name.trim(),
      receiver_last_name: form.receiver_last_name.trim(),
      receiver_patronymic: form.receiver_patronymic.trim(),
      receiver_phone: form.receiver_phone.trim(),
      receiver_email: form.receiver_email.trim(),
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
        <Box component="form" onSubmit={handleSubmit} noValidate>
          <Stack spacing={3}>
            {formError && <Alert severity="error">{formError}</Alert>}

            <Typography variant="h6" fontWeight={700}>
              Дані відправлення
            </Typography>

            <LocationSelector
              value={form.destination}
              onChange={(value) => updateField('destination', value)}
              onBlur={() => touchField('destination')}
              label="Локація призначення"
              params={{ type: 'post_office' }}
              required
              error={getFieldError('destination')}
              helperText={getFieldHelper('destination')}
            />

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Вага"
                type="number"
                value={form.weight}
                onChange={(e) => updateField('weight', e.target.value)}
                onBlur={() => touchField('weight')}
                inputProps={{ min: 0.001, step: '0.001' }}
                required
                error={getFieldError('weight')}
                helperText={getFieldHelper('weight')}
              />

              <Select
                label="Тип оплати"
                value={form.payment_type}
                onChange={(e) => updateField('payment_type', e.target.value)}
                options={[
                  { value: 'prepaid', label: 'Відправник сплачує' },
                  { value: 'cash_on_delivery', label: 'Отримувач сплачує' },
                ]}
                helperText={getFieldHelper('payment_type')}
                required
              />
            </Stack>

            <Input
              label="Опис"
              value={form.description}
              onChange={(e) => updateField('description', e.target.value)}
              helperText={getFieldHint('description')}
              placeholder="Наприклад: документи, одяг, техніка"
              multiline
              minRows={3}
            />

            <Typography variant="h6" fontWeight={700}>
              Відправник
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Прізвище"
                value={form.sender_last_name}
                onChange={(e) => updateField('sender_last_name', e.target.value)}
                onBlur={() => touchField('sender_last_name')}
                required
                error={getFieldError('sender_last_name')}
                helperText={getFieldHelper('sender_last_name')}
              />
              <Input
                label="Ім’я"
                value={form.sender_first_name}
                onChange={(e) => updateField('sender_first_name', e.target.value)}
                onBlur={() => touchField('sender_first_name')}
                required
                error={getFieldError('sender_first_name')}
                helperText={getFieldHelper('sender_first_name')}
              />
              <Input
                label="По батькові"
                value={form.sender_patronymic}
                onChange={(e) => updateField('sender_patronymic', e.target.value)}
                onBlur={() => touchField('sender_patronymic')}
                required
                error={getFieldError('sender_patronymic')}
                helperText={getFieldHelper('sender_patronymic')}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Телефон"
                value={form.sender_phone}
                onChange={(e) => updateField('sender_phone', e.target.value)}
                onBlur={() => touchField('sender_phone')}
                required
                error={getFieldError('sender_phone')}
                helperText={getFieldHelper('sender_phone')}
                placeholder="+380501234567"
              />
              <Input
                label="Email"
                type="email"
                value={form.sender_email}
                onChange={(e) => updateField('sender_email', e.target.value)}
                onBlur={() => touchField('sender_email')}
                error={getFieldError('sender_email')}
                helperText={getFieldHelper('sender_email')}
                placeholder="sender@example.com"
              />
            </Stack>

            <Typography variant="h6" fontWeight={700}>
              Отримувач
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Прізвище"
                value={form.receiver_last_name}
                onChange={(e) => updateField('receiver_last_name', e.target.value)}
                onBlur={() => touchField('receiver_last_name')}
                required
                error={getFieldError('receiver_last_name')}
                helperText={getFieldHelper('receiver_last_name')}
              />
              <Input
                label="Ім’я"
                value={form.receiver_first_name}
                onChange={(e) => updateField('receiver_first_name', e.target.value)}
                onBlur={() => touchField('receiver_first_name')}
                required
                error={getFieldError('receiver_first_name')}
                helperText={getFieldHelper('receiver_first_name')}
              />
              <Input
                label="По батькові"
                value={form.receiver_patronymic}
                onChange={(e) => updateField('receiver_patronymic', e.target.value)}
                onBlur={() => touchField('receiver_patronymic')}
                required
                error={getFieldError('receiver_patronymic')}
                helperText={getFieldHelper('receiver_patronymic')}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Input
                label="Телефон"
                value={form.receiver_phone}
                onChange={(e) => updateField('receiver_phone', e.target.value)}
                onBlur={() => touchField('receiver_phone')}
                required
                error={getFieldError('receiver_phone')}
                helperText={getFieldHelper('receiver_phone')}
                placeholder="+380501234567"
              />
              <Input
                label="Email"
                type="email"
                value={form.receiver_email}
                onChange={(e) => updateField('receiver_email', e.target.value)}
                onBlur={() => touchField('receiver_email')}
                error={getFieldError('receiver_email')}
                helperText={getFieldHelper('receiver_email')}
                placeholder="receiver@example.com"
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
