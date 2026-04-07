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

const downloadReport = async (url, fallbackFilename, params) => {
  const response = await client.get(url, {
    params,
    responseType: 'blob',
  })

  const filename = getFilenameFromDisposition(
    response.headers['content-disposition'],
    fallbackFilename
  )

  downloadBlobFile(response.data, filename)
  return { ok: true, filename }
}

export const apiDownloadShipmentBarcode = (id) =>
  downloadReport(`/reports/shipment/${id}/barcode/`, `barcode_${id}.pdf`)

export const apiDownloadShipmentReceipt = (id) =>
  downloadReport(`/reports/shipment/${id}/receipt/`, `receipt_${id}.pdf`)

export const apiDownloadShipmentDeliveryReport = (id) =>
  downloadReport(`/reports/shipment/${id}/delivery/`, `delivery_${id}.pdf`)

export const apiDownloadShipmentPaymentReport = (id) =>
  downloadReport(`/reports/shipment/${id}/payment/`, `payment_${id}.pdf`)

export const apiDownloadDispatchDepartReport = (id) =>
  downloadReport(`/reports/dispatch/${id}/depart/`, `dispatch_depart_${id}.pdf`)

export const apiDownloadDispatchArriveReport = (id) =>
  downloadReport(`/reports/dispatch/${id}/arrive/`, `dispatch_arrive_${id}.pdf`)

export const apiDownloadLocationReport = (params = {}) =>
  downloadReport('/reports/location/', 'location_report.pdf', params)
