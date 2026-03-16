import api from './axios'
export const apiPublicTrack    = (num)  => api.get(`/tracking/public/${num}/`).then(r => r.data)
export const apiGetEvents      = (id)   => api.get('/tracking/events/', { params: { shipment: id } }).then(r => r.data)
