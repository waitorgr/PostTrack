const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^\+?[0-9()\-\s]{10,20}$/

export function isBlank(value) {
  return String(value ?? '').trim() === ''
}

export function validateRequired(value, label) {
  if (isBlank(value)) {
    return `Поле «${label}» є обов’язковим`
  }
  return ''
}

export function validateWeight(value) {
  if (isBlank(value)) {
    return 'Вкажіть вагу посилки'
  }

  const numericValue = Number(value)

  if (Number.isNaN(numericValue)) {
    return 'Вага повинна бути числом'
  }

  if (numericValue <= 0) {
    return 'Вага повинна бути більшою за 0'
  }

  return ''
}

export function validatePhone(value, label = 'Телефон') {
  if (isBlank(value)) {
    return `Поле «${label}» є обов’язковим`
  }

  if (!PHONE_RE.test(String(value).trim())) {
    return `Некоректний формат поля «${label}». Приклад: +380501234567`
  }

  return ''
}

export function validateEmail(value, label = 'Email', required = false) {
  if (isBlank(value)) {
    return required ? `Поле «${label}» є обов’язковим` : ''
  }

  if (!EMAIL_RE.test(String(value).trim())) {
    return `Некоректний формат поля «${label}»`
  }

  return ''
}

export function validateDestination(value) {
  if (!value?.id) {
    return 'Оберіть відділення призначення'
  }
  return ''
}

export function validateFullNamePart(value, label) {
  const requiredError = validateRequired(value, label)
  if (requiredError) {
    return requiredError
  }

  if (String(value).trim().length < 2) {
    return `Поле «${label}» має містити щонайменше 2 символи`
  }

  return ''
}

export function mapApiErrorsToForm(errorData, knownFields = []) {
  if (!errorData || typeof errorData !== 'object') {
    return { fieldErrors: {}, generalError: '' }
  }

  const fieldErrors = {}
  let generalError = ''

  for (const [key, value] of Object.entries(errorData)) {
    const message = Array.isArray(value) ? value.join(' ') : String(value)

    if (knownFields.includes(key)) {
      fieldErrors[key] = message
    } else if (key === 'detail' || key === 'non_field_errors') {
      generalError = message
    }
  }

  if (!generalError && !Object.keys(fieldErrors).length) {
    generalError = Object.values(errorData)
      .flat()
      .filter(Boolean)
      .join(' ')
  }

  return { fieldErrors, generalError }
}
