import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  apiGetRoutes,
  apiGetRoute,
  apiCreateRoute,
  apiUpdateRoute,
  apiConfirmRoute,
  apiStartRoute,
  apiCompleteRoute,
  apiGenerateDefaultRouteSteps,
  apiMarkRouteStepArrival,
  apiMarkRouteStepDeparture,
} from '../api/routes'

export function useRoutes(params) {
  return useQuery({
    queryKey: ['routes', params],
    queryFn: () => apiGetRoutes(params),
  })
}

export function useRoute(id) {
  return useQuery({
    queryKey: ['route', id],
    queryFn: () => apiGetRoute(id),
    enabled: Boolean(id),
  })
}

export function useCreateRoute() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiCreateRoute,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
    },
  })
}

export function useUpdateRoute() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }) => apiUpdateRoute(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', variables.id] })
    },
  })
}

export function useConfirmRoute() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiConfirmRoute,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', id] })
    },
  })
}

export function useStartRoute() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiStartRoute,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', id] })
    },
  })
}

export function useCompleteRoute() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiCompleteRoute,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', id] })
    },
  })
}

export function useGenerateDefaultRouteSteps() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiGenerateDefaultRouteSteps,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', id] })
    },
  })
}

export function useMarkRouteStepArrival() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ routeId, data }) => apiMarkRouteStepArrival(routeId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', variables.routeId] })
    },
  })
}

export function useMarkRouteStepDeparture() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ routeId, data }) => apiMarkRouteStepDeparture(routeId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['routes'] })
      queryClient.invalidateQueries({ queryKey: ['route', variables.routeId] })
    },
  })
}