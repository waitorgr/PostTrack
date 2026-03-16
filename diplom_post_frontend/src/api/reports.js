const downloadPDF = async (url, filename) => {
  const token = localStorage.getItem('access')
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) throw new Error('Помилка завантаження PDF')
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
}

export const downloadReceipt       = (id) => downloadPDF(`/api/reports/shipment/${id}/receipt/`,  `receipt_${id}.pdf`)
export const downloadDelivery      = (id) => downloadPDF(`/api/reports/shipment/${id}/delivery/`, `delivery_${id}.pdf`)
export const downloadPayment       = (id) => downloadPDF(`/api/reports/shipment/${id}/payment/`,  `payment_${id}.pdf`)
export const downloadDispatchDepart= (id) => downloadPDF(`/api/reports/dispatch/${id}/depart/`,   `dispatch_depart_${id}.pdf`)
export const downloadDispatchArrive= (id) => downloadPDF(`/api/reports/dispatch/${id}/arrive/`,   `dispatch_arrive_${id}.pdf`)
export const downloadLocationReport= (params = '') =>
  downloadPDF(`/api/reports/location/${params ? '?' + params : ''}`, 'location_report.pdf')
