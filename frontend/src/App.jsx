import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import LeaguesPage from './pages/LeaguesPage'
import SeasonsPage from './pages/SeasonsPage'
import DivisionsPage from './pages/DivisionsPage'
import TeamsPage from './pages/TeamsPage'
import PlayersPage from './pages/PlayersPage'
import RegistrationsPage from './pages/RegistrationsPage'
import RegisterTeamPage from './pages/RegisterTeamPage'
import RefereesPage from './pages/RefereesPage'
import MatchesPage from './pages/MatchesPage'
import StandingsPage from './pages/StandingsPage'
import StatisticsPage from './pages/StatisticsPage'
import ReportsPage from './pages/ReportsPage'
import ArchivePage from './pages/ArchivePage'
import SettingsPage from './pages/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function Protected({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<Protected><DashboardPage /></Protected>} />
          <Route path="/leagues" element={<Protected><LeaguesPage /></Protected>} />
          <Route path="/seasons" element={<Protected><SeasonsPage /></Protected>} />
          <Route path="/divisions" element={<Protected><DivisionsPage /></Protected>} />
          <Route path="/teams" element={<Protected><TeamsPage /></Protected>} />
          <Route path="/players" element={<Protected><PlayersPage /></Protected>} />
          <Route path="/registrations" element={<Protected><RegistrationsPage /></Protected>} />
          <Route path="/register-team" element={<Protected><RegisterTeamPage /></Protected>} />
          <Route path="/referees" element={<Protected><RefereesPage /></Protected>} />
          <Route path="/matches" element={<Protected><MatchesPage /></Protected>} />
          <Route path="/standings" element={<Protected><StandingsPage /></Protected>} />
          <Route path="/statistics" element={<Protected><StatisticsPage /></Protected>} />
          <Route path="/reports" element={<Protected><ReportsPage /></Protected>} />
          <Route path="/archive" element={<Protected><ArchivePage /></Protected>} />
          <Route path="/settings" element={<Protected><SettingsPage /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
