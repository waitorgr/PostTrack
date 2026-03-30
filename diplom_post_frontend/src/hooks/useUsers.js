import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  apiGetUsers,
  apiGetUser,
  apiCreateUser,
  apiUpdateUser,
  apiDeleteUser,
} from '../api/users'

export const userKeys = {
  all: ['users'],
  lists: () => [...userKeys.all, 'list'],
  list: (params) => [...userKeys.lists(), params],
  details: () => [...userKeys.all, 'detail'],
  detail: (id) => [...userKeys.details(), id],
}

export const useUsers = (params = {}) =>
  useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => apiGetUsers(params),
  })

export const useUser = (id) =>
  useQuery({
    queryKey: userKeys.detail(id),
    queryFn: () => apiGetUser(id),
    enabled: Boolean(id),
  })

export const useCreateUser = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiCreateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all })
    },
  })
}

export const useUpdateUser = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }) => apiUpdateUser(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: userKeys.all })
      queryClient.invalidateQueries({ queryKey: userKeys.detail(variables.id) })
    },
  })
}

export const useDeleteUser = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: apiDeleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.all })
    },
  })
}