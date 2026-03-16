import dayjs from 'dayjs'
import 'dayjs/locale/uk'
dayjs.locale('uk')

export const fDate = (d) => d ? dayjs(d).format('DD.MM.YYYY') : '—'
export const fDateTime = (d) => d ? dayjs(d).format('DD.MM.YYYY HH:mm') : '—'
export const fFromNow = (d) => d ? dayjs(d).fromNow() : '—'

export const STATUS_LABELS = {
  accepted:            'Прийнято',
  picked_up_by_driver: 'Забрано водієм',
  in_transit:          'В дорозі',
  arrived_at_facility: 'Прибуло до об\'єкту',
  sorted:              'Відсортовано',
  out_for_delivery:    'Передано для доставки',
  available_for_pickup:'Очікує отримання',
  delivered:           'Доставлено',
  cancelled:           'Скасовано',
  returned:            'Повернуто',
}

export const STATUS_COLORS = {
  accepted:            'default',
  picked_up_by_driver: 'info',
  in_transit:          'info',
  arrived_at_facility: 'info',
  sorted:              'warning',
  out_for_delivery:    'warning',
  available_for_pickup:'warning',
  delivered:           'success',
  cancelled:           'error',
  returned:            'error',
}

export const ROLE_LABELS = {
  customer:          'Клієнт',
  postal_worker:     'Працівник пошти',
  warehouse_worker:  'Працівник складу',
  driver:            'Водій',
  logist:            'Логіст',
  hr:                'HR',
  admin:             'Адміністратор',
}

export const DISPATCH_STATUS_LABELS = {
  forming:    'Формується',
  ready:      'Готово',
  in_transit: 'В дорозі',
  arrived:    'Прибуло',
  completed:  'Завершено',
}

export const DISPATCH_STATUS_COLORS = {
  forming:    'default',
  ready:      'warning',
  in_transit: 'info',
  arrived:    'success',
  completed:  'success',
}

export const ROUTE_STATUS_LABELS = {
  draft:       'Чернетка',
  confirmed:   'Підтверджено',
  in_progress: 'Виконується',
  completed:   'Виконано',
  cancelled:   'Скасовано',
}

export const ROUTE_STATUS_COLORS = {
  draft:       'default',
  confirmed:   'info',
  in_progress: 'warning',
  completed:   'success',
  cancelled:   'error',
}
