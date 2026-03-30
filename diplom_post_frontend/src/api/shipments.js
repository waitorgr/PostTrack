import client from './client'

export const apiGetShipments = (params) =>
  client.get('/shipments/', { params }).then((res) => res.data)

export const apiGetShipment = (id) =>
  client.get(`/shipments/${id}/`).then((res) => res.data)

export const apiCreateShipment = (data) =>
  client.post('/shipments/', data).then((res) => res.data)

export const apiCancelShipment = (id, reason) =>
  client.post(`/shipments/${id}/cancel/`, { reason }).then((res) => res.data)

export const apiConfirmDelivery = (id) =>
  client.post(`/shipments/${id}/confirm_delivery/`).then((res) => res.data)

export const apiConfirmPayment = (id) =>
  client.post(`/shipments/${id}/confirm_payment/`).then((res) => res.data)

export const apiUpdateShipmentStatus = (id, status, note = '') =>
  client.post(`/shipments/${id}/update_status/`, { status, note }).then((res) => res.data)