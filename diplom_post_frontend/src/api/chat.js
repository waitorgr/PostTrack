import api from './axios'
export const apiGetRooms    = ()      => api.get('/chat/rooms/').then(r => r.data)
export const apiCreateRoom  = (data)  => api.post('/chat/rooms/create/', data).then(r => r.data)
export const apiGetMessages = (id)    => api.get(`/chat/rooms/${id}/messages/`).then(r => r.data)
