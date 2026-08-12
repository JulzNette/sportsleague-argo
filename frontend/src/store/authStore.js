/**
 * Auth state, persisted to localStorage so a page refresh doesn't log the
 * user out. Only the JWT + role + email are kept client-side - the backend
 * is the only place that ever decides what a role can actually do.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      role: null,
      email: null,
      isAuthenticated: false,

      login: ({ access_token, role, email }) =>
        set({ token: access_token, role, email, isAuthenticated: true }),

      logout: () => set({ token: null, role: null, email: null, isAuthenticated: false }),
    }),
    { name: 'sportsleague-auth' }
  )
)
