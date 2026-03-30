import client from './client'

export const apiGetLocations = (params) =>
  client.get('/locations/', { params }).then((res) => res.data)