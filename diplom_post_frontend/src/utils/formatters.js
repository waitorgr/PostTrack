// src/utils/formatters.js
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/uk'

dayjs.extend(relativeTime)
dayjs.locale('uk')

export const fDate = (d) => (d ? dayjs(d).format('DD.MM.YYYY') : '—')
export const fDateTime = (d) => (d ? dayjs(d).format('DD.MM.YYYY HH:mm') : '—')
export const fFromNow = (d) => (d ? dayjs(d).fromNow() : '—')