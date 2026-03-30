import client from './client'

export const apiGetRoutes = (params) =>
  client.get('/logistics/routes/', { params }).then((res) => res.data)

export const apiGetRoute = (id) =>
  client.get(`/logistics/routes/${id}/`).then((res) => res.data)

export const apiCreateRoute = (data) =>
  client.post('/logistics/routes/', data).then((res) => res.data)

export const apiUpdateRoute = (id, data) =>
  client.patch(`/logistics/routes/${id}/`, data).then((res) => res.data)

export const apiConfirmRoute = (id) =>
  client.post(`/logistics/routes/${id}/confirm/`).then((res) => res.data)

export const apiStartRoute = (id) =>
  client.post(`/logistics/routes/${id}/start/`).then((res) => res.data)

export const apiCompleteRoute = (id) =>
  client.post(`/logistics/routes/${id}/complete/`).then((res) => res.data)

export const apiGenerateDefaultRouteSteps = (id) =>
  client.post(`/logistics/routes/${id}/generate_default_steps/`).then((res) => res.data)