import api from './axios'

export const apiGetShipments    = (params) => api.get('/shipments/', { params }).then(r => r.data)
export const apiGetShipment     = (id)     => api.get(`/shipments/${id}/`).then(r => r.data)
export const apiCreateShipment  = (data)   => api.post('/shipments/', data).then(r => r.data)
export const apiCancelShipment  = (id, reason) => api.post(`/shipments/${id}/cancel/`, { reason }).then(r => r.data)
export const apiConfirmDelivery = (id)     => api.post(`/shipments/${id}/confirm_delivery/`).then(r => r.data)
export const apiConfirmPayment  = (id)     => api.post(`/shipments/${id}/confirm_payment/`).then(r => r.data)
export const apiUpdateStatus    = (id, status, note) =>
  api.post(`/shipments/${id}/update_status/`, { status, note }).then(r => r.data)
