import client from './client'

export const apiLogin = (username, password) =>
  client.post('/accounts/login/', { username, password }).then((res) => res.data)

export const apiLogout = (refresh) =>
  client.post('/accounts/logout/', { refresh }).then((res) => res.data)

export const apiMe = () =>
  client.get('/accounts/me/').then((res) => res.data)

export const apiRegisterCustomer = (data) =>
  client.post('/accounts/register/', data).then((res) => res.data)

export async function apiGetMe() {
  const { data } = await api.get('/accounts/me/')
  return data
}

export async function apiGetLocationDetail(locationId) {
  const { data } = await api.get(`/locations/${locationId}/`)
  return data
}