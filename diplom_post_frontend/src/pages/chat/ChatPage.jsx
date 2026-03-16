import { useEffect, useRef, useState } from 'react'
import { Box, Card, List, ListItemButton, ListItemText, ListItemAvatar,
  Avatar, Typography, TextField, IconButton, Badge, Divider, CircularProgress } from '@mui/material'
import { SendRounded, ChatRounded } from '@mui/icons-material'
import { apiGetRooms, apiCreateRoom, apiGetMessages } from '../../api/chat'
import { apiGetWorkers } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'
import { fDateTime } from '../../utils/formatters'

export default function ChatPage() {
  const { user } = useAuthStore()
  const [rooms, setRooms] = useState([])
  const [activeRoom, setActiveRoom] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loadingRooms, setLoadingRooms] = useState(true)
  const wsRef = useRef(null)
  const bottomRef = useRef(null)
  const isDriver = user?.role === 'driver'
  const isLogist = user?.role === 'logist'

  const loadRooms = () => {
    setLoadingRooms(true)
    apiGetRooms().then(r => setRooms(r.results || r)).finally(() => setLoadingRooms(false))
  }

  useEffect(() => { loadRooms() }, [])

  const openRoom = async (room) => {
    // Close previous WS
    if (wsRef.current) wsRef.current.close()
    setActiveRoom(room)
    const msgs = await apiGetMessages(room.id)
    setMessages(msgs.results || msgs)

    // Connect WebSocket
    const token = localStorage.getItem('access')
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${room.id}/?token=${token}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          id: data.id, text: data.text,
          sender_name: data.sender_name,
          is_own: data.sender_id === user?.id,
          created_at: data.created_at,
        }])
      }
    }
  }

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = () => {
    if (!input.trim() || !wsRef.current) return
    wsRef.current.send(JSON.stringify({ text: input.trim() }))
    setInput('')
  }

  const handleKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }

  // Логіст може ініціювати чат з водіями
  const initDriverChat = async (driverId) => {
    try {
      const room = await apiCreateRoom({ driver_id: driverId })
      loadRooms()
      openRoom(room)
    } catch {}
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} color="primary.main" mb={3}>Чат</Typography>

      <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 160px)' }}>
        {/* Список кімнат */}
        <Card sx={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="subtitle2" fontWeight={700}>Розмови</Typography>
          </Box>
          {loadingRooms ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}><CircularProgress size={24} /></Box>
          ) : (
            <List disablePadding sx={{ flex: 1, overflowY: 'auto' }}>
              {rooms.length === 0 && (
                <Box sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Немає розмов</Typography>
                </Box>
              )}
              {rooms.map(room => {
                const name = isDriver ? room.logist_name : room.driver_name
                const unread = room.unread_count || 0
                return (
                  <ListItemButton key={room.id} selected={activeRoom?.id === room.id}
                    onClick={() => openRoom(room)} sx={{ borderRadius: 0 }}>
                    <ListItemAvatar>
                      <Badge badgeContent={unread} color="error">
                        <Avatar sx={{ width: 36, height: 36, bgcolor: 'primary.main', fontSize: 13, fontWeight: 700 }}>
                          {name?.split(' ').map(w => w[0]).slice(0, 2).join('')}
                        </Avatar>
                      </Badge>
                    </ListItemAvatar>
                    <ListItemText
                      primary={<Typography variant="body2" fontWeight={unread ? 700 : 500} noWrap>{name}</Typography>}
                      secondary={<Typography variant="caption" noWrap color="text.secondary">
                        {room.last_message?.text || 'Немає повідомлень'}
                      </Typography>}
                    />
                  </ListItemButton>
                )
              })}
            </List>
          )}
        </Card>

        {/* Область повідомлень */}
        <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {!activeRoom ? (
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
              <ChatRounded sx={{ fontSize: 48, color: 'text.disabled' }} />
              <Typography color="text.secondary">Оберіть розмову</Typography>
            </Box>
          ) : (
            <>
              <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
                <Typography variant="subtitle2" fontWeight={700}>
                  {isDriver ? activeRoom.logist_name : activeRoom.driver_name}
                </Typography>
              </Box>

              <Box sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
                {messages.map(msg => (
                  <Box key={msg.id} sx={{ display: 'flex', justifyContent: msg.is_own ? 'flex-end' : 'flex-start' }}>
                    <Box sx={{
                      maxWidth: '70%', px: 1.5, py: 1, borderRadius: 2,
                      bgcolor: msg.is_own ? 'primary.main' : '#F1F5F9',
                      color: msg.is_own ? 'white' : 'text.primary',
                    }}>
                      {!msg.is_own && (
                        <Typography variant="caption" fontWeight={700} display="block" mb={0.3} opacity={0.8}>
                          {msg.sender_name}
                        </Typography>
                      )}
                      <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>{msg.text}</Typography>
                      <Typography variant="caption" display="block" textAlign="right" mt={0.3}
                        sx={{ opacity: 0.6, fontSize: '0.65rem' }}>
                        {fDateTime(msg.created_at)}
                      </Typography>
                    </Box>
                  </Box>
                ))}
                <div ref={bottomRef} />
              </Box>

              <Divider />
              <Box sx={{ p: 1.5, display: 'flex', gap: 1 }}>
                <TextField fullWidth multiline maxRows={3} size="small" placeholder="Написати повідомлення..."
                  value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey} />
                <IconButton color="primary" onClick={send} disabled={!input.trim()}>
                  <SendRounded />
                </IconButton>
              </Box>
            </>
          )}
        </Card>
      </Box>
    </Box>
  )
}
