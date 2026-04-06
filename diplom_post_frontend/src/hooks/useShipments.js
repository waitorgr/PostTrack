import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  apiGetShipments,
  apiGetShipment,
  apiCreateShipment,
  apiCancelShipment,
  apiConfirmDelivery,
  apiConfirmPayment,
  apiUpdateShipmentStatus,
  apiManualSortShipment,
} from '../api/shipments'

export const shipmentKeys = {
  all: ['shipments'],
  lists: () => [...shipmentKeys.all, 'list'],
  list: (params) => [...shipmentKeys.lists(), params],
  details: () => [...shipmentKeys.all, 'detail'],
  detail: (id) => [...shipmentKeys.details(), id],
}

export const useShipments = (params = {}) =>
  useQuery({
    queryKey: shipmentKeys.list(params),
    queryFn: () => apiGetShipments(params),
  })

export const useShipment = (id) =>
  useQuery({
    queryKey: shipmentKeys.detail(id),
    queryFn: () => apiGetShipment(id),
    enabled: Boolean(id),
  })

export const useCreateShipment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiCreateShipment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shipmentKeys.all })
    },
  })
}

export const useCancelShipment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, reason }) => apiCancelShipment(id, reason),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: shipmentKeys.all })
      queryClient.invalidateQueries({ queryKey: shipmentKeys.detail(variables.id) })
    },
  })
}

export const useConfirmShipmentDelivery = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiConfirmDelivery,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shipmentKeys.all })
      queryClient.invalidateQueries({ queryKey: shipmentKeys.detail(id) })
    },
  })
}

export const useConfirmShipmentPayment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiConfirmPayment,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shipmentKeys.all })
      queryClient.invalidateQueries({ queryKey: shipmentKeys.detail(id) })
    },
  })
}

export const useUpdateShipmentStatus = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, status, note }) => apiUpdateShipmentStatus(id, status, note),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: shipmentKeys.all })
      queryClient.invalidateQueries({ queryKey: shipmentKeys.detail(variables.id) })
    },
  })
}

export const useManualSortShipment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiManualSortShipment,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: shipmentKeys.all })
      queryClient.invalidateQueries({ queryKey: shipmentKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: ['warehouse'] })
      queryClient.invalidateQueries({ queryKey: ['dispatch-groups'] })
    },
  })
}
