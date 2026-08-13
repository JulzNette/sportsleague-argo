/**
 * Single axios instance for the whole app. Attaches the JWT from the auth
 * store to every request, and logs the user out on a 401 (expired/invalid
 * token) so they land back on the login screen instead of seeing broken
 * pages.
 */
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8020/api/v1'

export const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

// Thin wrappers per resource - keeps query/mutation hooks short and gives
// one place to change a URL if the backend route ever moves.
export const endpoints = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),

  leagues: {
    list: () => api.get('/leagues'),
    get: (id) => api.get(`/leagues/${id}`),
    create: (data) => api.post('/leagues', data),
    update: (id, data) => api.patch(`/leagues/${id}`, data),
    remove: (id) => api.delete(`/leagues/${id}`),
    archived: () => api.get('/leagues/archived'),
    restore: (id) => api.post(`/leagues/${id}/restore`),
    purge: (id) => api.delete(`/leagues/${id}/purge`),
  },
  seasons: {
    list: (params) => api.get('/seasons', { params }),
    create: (data) => api.post('/seasons', data),
    update: (id, data) => api.patch(`/seasons/${id}`, data),
    remove: (id) => api.delete(`/seasons/${id}`),
    archived: () => api.get('/seasons/archived'),
    restore: (id) => api.post(`/seasons/${id}/restore`),
    purge: (id) => api.delete(`/seasons/${id}/purge`),
  },
  divisions: {
    list: (params) => api.get('/divisions', { params }),
    create: (data) => api.post('/divisions', data),
    update: (id, data) => api.patch(`/divisions/${id}`, data),
    remove: (id) => api.delete(`/divisions/${id}`),
    archived: () => api.get('/divisions/archived'),
    restore: (id) => api.post(`/divisions/${id}/restore`),
    purge: (id) => api.delete(`/divisions/${id}/purge`),
  },
  teams: {
    list: (params) => api.get('/teams', { params }),
    create: (data) => api.post('/teams', data),
    update: (id, data) => api.patch(`/teams/${id}`, data),
    remove: (id) => api.delete(`/teams/${id}`),
    archived: () => api.get('/teams/archived'),
    restore: (id) => api.post(`/teams/${id}/restore`),
    purge: (id) => api.delete(`/teams/${id}/purge`),
  },
  players: {
    list: (params) => api.get('/players', { params }),
    create: (data) => api.post('/players', data),
    update: (id, data) => api.patch(`/players/${id}`, data),
    remove: (id) => api.delete(`/players/${id}`),
    archived: () => api.get('/players/archived'),
    restore: (id) => api.post(`/players/${id}/restore`),
    purge: (id) => api.delete(`/players/${id}/purge`),
  },
  referees: {
    list: () => api.get('/referees'),
    create: (data) => api.post('/referees', data),
    update: (id, data) => api.patch(`/referees/${id}`, data),
    remove: (id) => api.delete(`/referees/${id}`),
    archived: () => api.get('/referees/archived'),
    restore: (id) => api.post(`/referees/${id}/restore`),
    purge: (id) => api.delete(`/referees/${id}/purge`),
  },
  matches: {
    list: (params) => api.get('/matches', { params }),
    create: (data) => api.post('/matches', data),
    update: (id, data) => api.patch(`/matches/${id}`, data),
    assignReferee: (id, refereeId) =>
      api.post(`/matches/${id}/assign-referee`, null, { params: { referee_id: refereeId } }),
    setStatus: (id, status) => api.post(`/matches/${id}/status`, { status }),
    remove: (id) => api.delete(`/matches/${id}`),
    archived: () => api.get('/matches/archived'),
    restore: (id) => api.post(`/matches/${id}/restore`),
    purge: (id) => api.delete(`/matches/${id}/purge`),
  },
  results: {
    get: (matchId) => api.get(`/matches/${matchId}/result`),
    submit: (matchId, data) => api.post(`/matches/${matchId}/result`, data),
    update: (matchId, data) => api.patch(`/matches/${matchId}/result`, data),
  },
  standings: {
    get: (seasonId, divisionId) =>
      api.get('/standings', { params: { season_id: seasonId, division_id: divisionId } }),
  },
  reports: {
    list: () => api.get('/reports'),
    create: (data) => api.post('/reports', data),
    viewStandings: (id) => api.get(`/reports/${id}/standings`),
  },
}
