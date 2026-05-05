import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { usersApi } from '@/api/users'
import type { UserPublic } from '@/api/users'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<UserPublic | null>(null)

  function setToken(token: string) {
    accessToken.value = token
    localStorage.setItem('access_token', token)
  }

  function clearToken() {
    accessToken.value = null
    localStorage.removeItem('access_token')
    user.value = null
  }

  async function login(username: string, password: string): Promise<void> {
    const response = await axios.post<{ access_token: string }>(
      '/api/v1/auth/login',
      { username, password }
    )
    setToken(response.data.access_token)
    await fetchMe()
  }

  async function fetchMe(): Promise<void> {
    try {
      const response = await usersApi.getMe()
      user.value = response.data
    } catch {
      clearToken()
    }
  }

  async function refreshAccessToken(): Promise<string> {
    // Refresh token is stored in httpOnly cookie; the browser sends it automatically
    const response = await axios.post<{ access_token: string }>(
      '/api/v1/auth/refresh'
    )
    setToken(response.data.access_token)
    return response.data.access_token
  }

  function logout(): void {
    // Best-effort: call backend to revoke refresh token cookie
    axios.post('/api/v1/auth/logout').catch(() => {})
    clearToken()
  }

  return {
    accessToken,
    user,
    login,
    logout,
    fetchMe,
    refreshAccessToken,
    setToken,
    clearToken,
  }
})
