import api from './axios'
export const apiGetLocations = (params) => api.get('/locations/', { params }).then(r => r.data)
