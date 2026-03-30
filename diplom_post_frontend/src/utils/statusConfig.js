// src/utils/statusConfig.js

// =========================
// SHIPMENT STATUSES
// =========================
export const SHIPMENT_STATUS_LABELS = {
  accepted: 'Прийнято',
  picked_up_by_driver: 'Забрано водієм',
  in_transit: 'В дорозі',
  arrived_at_facility: "Прибуло до об'єкта",
  sorted: 'Відсортовано',
  out_for_delivery: 'Передано для доставки',
  available_for_pickup: 'Очікує отримання',
  delivered: 'Доставлено',
  cancelled: 'Скасовано',
  returned: 'Повернуто',
}

export const SHIPMENT_STATUS_COLORS = {
  accepted: 'default',
  picked_up_by_driver: 'info',
  in_transit: 'info',
  arrived_at_facility: 'info',
  sorted: 'warning',
  out_for_delivery: 'warning',
  available_for_pickup: 'warning',
  delivered: 'success',
  cancelled: 'error',
  returned: 'error',
}

// Для сумісності з поточним кодом
export const STATUS_LABELS = SHIPMENT_STATUS_LABELS
export const STATUS_COLORS = SHIPMENT_STATUS_COLORS

// =========================
// DISPATCH STATUSES
// =========================
export const DISPATCH_STATUS_LABELS = {
  forming: 'Формується',
  ready: 'Готово',
  in_transit: 'В дорозі',
  arrived: 'Прибуло',
  completed: 'Завершено',
}

export const DISPATCH_STATUS_COLORS = {
  forming: 'default',
  ready: 'warning',
  in_transit: 'info',
  arrived: 'success',
  completed: 'success',
}

// =========================
// ROUTE STATUSES
// =========================
export const ROUTE_STATUS_LABELS = {
  draft: 'Чернетка',
  confirmed: 'Підтверджено',
  in_progress: 'Виконується',
  completed: 'Виконано',
  cancelled: 'Скасовано',
}

export const ROUTE_STATUS_COLORS = {
  draft: 'default',
  confirmed: 'info',
  in_progress: 'warning',
  completed: 'success',
  cancelled: 'error',
}