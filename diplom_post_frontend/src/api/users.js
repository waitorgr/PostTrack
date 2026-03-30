import client from './client'

export const apiGetUsers = (params) =>
  client.get('/accounts/workers/', { params }).then((res) => res.data)

export const apiGetDrivers = (params = {}) =>
  client.get('/accounts/workers/drivers/', { params }).then((res) => res.data)

export const apiGetUser = (id) =>
  client.get(`/accounts/workers/${id}/`).then((res) => res.data)

export const apiCreateUser = (data) =>
  client.post('/accounts/workers/', data).then((res) => res.data)

export const apiUpdateUser = (id, data) =>
  client.patch(`/accounts/workers/${id}/`, data).then((res) => res.data)

export const apiDeleteUser = (id) =>
  client.delete(`/accounts/workers/${id}/`).then((res) => res.data)