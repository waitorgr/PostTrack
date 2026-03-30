import client from './client'

export const apiGetDispatchGroups = (params) =>
  client.get('/dispatch/groups/', { params }).then((res) => res.data)

export const apiGetDispatchGroup = (id) =>
  client.get(`/dispatch/groups/${id}/`).then((res) => res.data)

export const apiCreateDispatchGroup = (data) =>
  client.post('/dispatch/groups/', data).then((res) => res.data)

export const apiAddShipmentToDispatch = (id, tracking_number) =>
  client.post(`/dispatch/groups/${id}/add_shipment/`, { tracking_number }).then((res) => res.data)

export const apiRemoveShipmentFromDispatch = (id, tracking_number) =>
  client.post(`/dispatch/groups/${id}/remove_shipment/`, { tracking_number }).then((res) => res.data)

export const apiMarkDispatchReady = (id) =>
  client.post(`/dispatch/groups/${id}/mark_ready/`).then((res) => res.data)

export const apiDepartDispatch = (id) =>
  client.post(`/dispatch/groups/${id}/depart/`).then((res) => res.data)

export const apiArriveDispatch = (id) =>
  client.post(`/dispatch/groups/${id}/arrive/`).then((res) => res.data)
