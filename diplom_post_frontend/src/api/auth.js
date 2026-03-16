import api from './axios'

export const apiLogin  = (username, password) =>
  api.post('/accounts/login/', { username, password }).then(r => r.data)

export const apiLogout = (refresh) =>
  api.post('/accounts/logout/', { refresh })

export const apiMe = () =>
  api.get('/accounts/me/').then(r => r.data)

export const apiRegisterCustomer = (data) =>
  api.post('/accounts/register/', data).then(r => r.data)

export const apiGetWorkers = (params) =>
  api.get('/accounts/workers/', { params }).then(r => r.data)

export const apiCreateWorker = (data) =>
  api.post('/accounts/workers/', data).then(r => r.data)

export const apiUpdateWorker = (id, data) =>
  api.patch(`/accounts/workers/${id}/`, data).then(r => r.data)

export const apiDeleteWorker = (id) =>
  api.delete(`/accounts/workers/${id}/`)
