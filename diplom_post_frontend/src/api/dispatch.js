import client from './client'

const getFilenameFromDisposition = (contentDisposition, fallback) => {
  if (!contentDisposition) {
    return fallback
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1])
  }

  const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i)
  if (plainMatch?.[1]) {
    return plainMatch[1]
  }

  return fallback
}

const downloadBlobFile = (blob, filename) => {
  const objectUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(objectUrl)
}

const postDispatchPdfAction = async (url, fallbackFilename) => {
  const response = await client.post(url, null, { responseType: 'blob' })
  const filename = getFilenameFromDisposition(
    response.headers['content-disposition'],
    fallbackFilename
  )

  downloadBlobFile(response.data, filename)
  return { ok: true, filename }
}

export const apiGetDispatchGroups = (params) =>
  client.get('/dispatch/groups/', { params }).then((res) => res.data)

export const apiGetDispatchGroup = (id) =>
  client.get(`/dispatch/groups/${id}/`).then((res) => res.data)

export const apiAddShipmentToDispatch = (id, tracking_number) =>
  client.post(`/dispatch/groups/${id}/add_shipment/`, { tracking_number }).then((res) => res.data)

export const apiRemoveShipmentFromDispatch = (id, tracking_number) =>
  client.post(`/dispatch/groups/${id}/remove_shipment/`, { tracking_number }).then((res) => res.data)

export const apiMarkDispatchReady = (id) =>
  client.post(`/dispatch/groups/${id}/mark_ready/`).then((res) => res.data)

export const apiDepartDispatch = (id) =>
  postDispatchPdfAction(`/dispatch/groups/${id}/depart/`, `dispatch_depart_${id}.pdf`)

export const apiArriveDispatch = (id) =>
  postDispatchPdfAction(`/dispatch/groups/${id}/arrive/`, `dispatch_arrive_${id}.pdf`)

export const apiCreateDispatchGroup = (data) =>
  client.post('/dispatch/groups/create_with_shipment/', data).then((res) => res.data)

export const apiDeleteDispatchGroup = (id) =>
  client.delete(`/dispatch/groups/${id}/`).then((res) => res.data)
