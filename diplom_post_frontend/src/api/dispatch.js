import api from './axios'
export const apiGetGroups      = (params) => api.get('/dispatch/groups/', { params }).then(r => r.data)
export const apiGetGroup       = (id)     => api.get(`/dispatch/groups/${id}/`).then(r => r.data)
export const apiCreateGroup    = (data)   => api.post('/dispatch/groups/', data).then(r => r.data)
export const apiAddShipment    = (id, tracking_number) =>
  api.post(`/dispatch/groups/${id}/add_shipment/`, { tracking_number }).then(r => r.data)
export const apiRemoveShipment = (id, tracking_number) =>
  api.post(`/dispatch/groups/${id}/remove_shipment/`, { tracking_number }).then(r => r.data)
export const apiMarkReady      = (id)     => api.post(`/dispatch/groups/${id}/mark_ready/`).then(r => r.data)
export const apiDepart         = (id)     => api.post(`/dispatch/groups/${id}/depart/`).then(r => r.data)
export const apiArrive         = (id)     => api.post(`/dispatch/groups/${id}/arrive/`).then(r => r.data)
