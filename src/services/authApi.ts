import { apiRequest } from './api'

export type RoleName = 'student' | 'worker' | 'elder'

export interface UserProfile {
  user_id: string
  birthday: string
  role: RoleName
  first_test_completed: boolean
}

export function register(payload: {
  user_id: string
  password: string
  birthday: string
  role: RoleName
}): Promise<UserProfile> {
  return apiRequest<UserProfile>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function login(payload: { user_id: string; password: string }): Promise<UserProfile> {
  return apiRequest<UserProfile>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function markFirstTestCompleted(userId: string): Promise<UserProfile> {
  return apiRequest<UserProfile>(`/auth/users/${encodeURIComponent(userId)}/first-test`, {
    method: 'PATCH',
    body: JSON.stringify({ first_test_completed: true })
  })
}

