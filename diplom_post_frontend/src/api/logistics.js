import api from './axios'
export const apiGetRoutes    = (params) => api.get('/logistics/routes/', { params }).then(r => r.data)
export const apiGetRoute     = (id)     => api.get(`/logistics/routes/${id}/`).then(r => r.data)
export const apiCreateRoute  = (data)   => api.post('/logistics/routes/', data).then(r => r.data)
export const apiUpdateRoute  = (id, data) => api.patch(`/logistics/routes/${id}/`, data).then(r => r.data)
export const apiConfirmRoute = (id)     => api.post(`/logistics/routes/${id}/confirm/`).then(r => r.data)
export const apiStartRoute   = (id)     => api.post(`/logistics/routes/${id}/start/`).then(r => r.data)
export const apiCompleteRoute= (id)     => api.post(`/logistics/routes/${id}/complete/`).then(r => r.data)
