import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import {
  Search, Bell, Plus, User, LogOut, Menu, X,
  ShoppingBag, Home, MessageSquare, LayoutDashboard
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import clsx from 'clsx'

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navLinks = [
    { to: '/browse', label: 'Browse', icon: Search },
    { to: '/browse?type=RENTAL', label: 'Rentals', icon: Home },
    { to: '/browse?type=SALE', label: 'Marketplace', icon: ShoppingBag },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Navbar ───────────────────────────── */}
      <header className="sticky top-0 z-50 bg-brand-offwhite/90 backdrop-blur-md border-b border-black/5">
        <div className="page-container">
          <div className="flex items-center justify-between h-16">

            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 bg-brand-orange rounded-lg flex items-center justify-center
                              group-hover:rotate-12 transition-transform duration-200">
                <span className="text-white font-display font-bold text-sm">CL</span>
              </div>
              <span className="font-display font-bold text-xl text-brand-ink">
                Campus<span className="text-brand-orange">Loop</span>
              </span>
            </Link>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  className={clsx(
                    'px-4 py-2 rounded-lg font-body font-medium text-sm transition-colors duration-150',
                    isActive(to)
                      ? 'bg-brand-orange/10 text-brand-orange'
                      : 'text-brand-ink/60 hover:text-brand-ink hover:bg-black/5'
                  )}
                >
                  {label}
                </Link>
              ))}
            </nav>

            {/* Right side */}
            <div className="flex items-center gap-2">
              {isAuthenticated ? (
                <>
                  {/* Post listing button */}
                  <Link to="/create" className="hidden sm:flex btn-primary btn-sm gap-1.5">
                    <Plus size={16} />
                    Post
                  </Link>

                  {/* Messages */}
                  <Link to="/messages"
                    className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-black/5 transition-colors relative">
                    <MessageSquare size={18} className="text-brand-ink/70" />
                  </Link>

                  {/* Dashboard */}
                  <Link to="/dashboard"
                    className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-black/5 transition-colors">
                    <LayoutDashboard size={18} className="text-brand-ink/70" />
                  </Link>

                  {/* Profile dropdown */}
                  <div className="relative">
                    <button
                      onClick={() => setProfileOpen(!profileOpen)}
                      className="w-9 h-9 rounded-lg overflow-hidden border-2 border-transparent
                                 hover:border-brand-orange transition-colors duration-150"
                    >
                      {user?.avatar_url ? (
                        <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-brand-ink flex items-center justify-center">
                          <span className="text-white font-display font-bold text-sm">
                            {user?.first_name?.[0]}
                          </span>
                        </div>
                      )}
                    </button>

                    {profileOpen && (
                      <div className="absolute right-0 top-11 w-52 card p-1.5 z-50 animate-fade-in">
                        <div className="px-3 py-2 border-b border-black/5 mb-1">
                          <p className="font-display font-semibold text-sm text-brand-ink">{user?.first_name} {user?.last_name}</p>
                          <p className="text-xs text-brand-ink/50 font-mono">{user?.university}</p>
                        </div>
                        <Link to={`/profile/${user?.id}`}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-black/5 transition-colors"
                          onClick={() => setProfileOpen(false)}>
                          <User size={14} /> My Profile
                        </Link>
                        <Link to="/dashboard"
                          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-black/5 transition-colors"
                          onClick={() => setProfileOpen(false)}>
                          <LayoutDashboard size={14} /> Dashboard
                        </Link>
                        <button onClick={handleLogout}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors">
                          <LogOut size={14} /> Log Out
                        </button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn-ghost btn-sm hidden sm:flex">Log in</Link>
                  <Link to="/register" className="btn-primary btn-sm">Sign up free</Link>
                </>
              )}

              {/* Mobile menu toggle */}
              <button
                className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg hover:bg-black/5"
                onClick={() => setMobileOpen(!mobileOpen)}
              >
                {mobileOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile nav */}
        {mobileOpen && (
          <div className="md:hidden border-t border-black/5 bg-brand-offwhite px-4 py-4 space-y-1 animate-slide-up">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link key={to} to={to}
                className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-black/5 font-body font-medium"
                onClick={() => setMobileOpen(false)}>
                <Icon size={18} className="text-brand-orange" />
                {label}
              </Link>
            ))}
            {isAuthenticated ? (
              <Link to="/create"
                className="flex items-center gap-3 px-4 py-3 rounded-xl bg-brand-orange text-white font-display font-semibold"
                onClick={() => setMobileOpen(false)}>
                <Plus size={18} /> Post a Listing
              </Link>
            ) : (
              <Link to="/register"
                className="flex items-center gap-3 px-4 py-3 rounded-xl bg-brand-orange text-white font-display font-semibold"
                onClick={() => setMobileOpen(false)}>
                Sign up free
              </Link>
            )}
          </div>
        )}
      </header>

      {/* ── Page content ─────────────────────── */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* ── Footer ───────────────────────────── */}
      <footer className="bg-brand-ink text-brand-offwhite mt-20">
        <div className="page-container py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-7 h-7 bg-brand-orange rounded-md flex items-center justify-center">
                  <span className="text-white font-display font-bold text-xs">CL</span>
                </div>
                <span className="font-display font-bold text-lg">CampusLoop</span>
              </div>
              <p className="text-sm text-white/50 font-body leading-relaxed">
                The marketplace built exclusively for verified college students.
              </p>
            </div>
            {[
              { title: 'Marketplace', links: ['Browse All', 'Rentals', 'For Sale', 'Services'] },
              { title: 'Account',     links: ['Sign Up', 'Log In', 'Dashboard', 'Post Listing'] },
              { title: 'About',       links: ['How it Works', 'Safety Tips', 'Contact'] },
            ].map(({ title, links }) => (
              <div key={title}>
                <h4 className="font-display font-semibold text-sm mb-3 text-white/70">{title}</h4>
                <ul className="space-y-2">
                  {links.map((l) => (
                    <li key={l}>
                      <a href="#" className="text-sm text-white/40 hover:text-white transition-colors">{l}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="mt-10 pt-6 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-xs text-white/30 font-mono">© 2025 CampusLoop. All rights reserved.</p>
            <p className="text-xs text-white/30 font-mono">.edu emails only — keeping it campus.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}