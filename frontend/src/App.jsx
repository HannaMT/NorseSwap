import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore'

import Layout from './components/layout/Layout'
import ProtectedRoute from './components/layout/ProtectedRoute'

import LandingPage    from './pages/LandingPage'
import LoginPage      from './pages/LoginPage'
import RegisterPage   from './pages/RegisterPage'
import BrowsePage     from './pages/BrowsePage'
import ListingPage    from './pages/ListingPage'
import CreateListing  from './pages/CreateListing'
import DashboardPage  from './pages/DashboardPage'
import ProfilePage    from './pages/ProfilePage'
import MessagesPage   from './pages/MessagesPage'

export default function App() {
  const init = useAuthStore((s) => s.init)

  useEffect(() => { init() }, [init])

  return (
    <Routes>
      {/* Public */}
      <Route path="/"         element={<LandingPage />} />
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Main app layout */}
      <Route element={<Layout />}>
        <Route path="/browse"           element={<BrowsePage />} />
        <Route path="/listings/:id"     element={<ListingPage />} />
        <Route path="/profile/:id"      element={<ProfilePage />} />

        {/* Protected — requires login */}
        <Route element={<ProtectedRoute />}>
          <Route path="/create"         element={<CreateListing />} />
          <Route path="/dashboard"      element={<DashboardPage />} />
          <Route path="/dashboard/:tab" element={<DashboardPage />} />
          <Route path="/messages"       element={<MessagesPage />} />
          <Route path="/messages/:id"   element={<MessagesPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}