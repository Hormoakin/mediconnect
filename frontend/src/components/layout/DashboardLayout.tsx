// ══════════════════════════════════════════════════════════════
// frontend/src/components/layout/DashboardLayout.tsx
//
// Shared authenticated shell for all four roles. The sidebar
// navigation items are role-aware (FR-01.3), so a patient never
// even SEES a link to the admin user-management screen, etc.
// ══════════════════════════════════════════════════════════════
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Stethoscope, MessageCircle, FileText,
  Search, LogOut, Menu, X, Activity, Bell,
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useSocket } from '../../contexts/SocketContext'
import clsx from 'clsx'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
  roles: Array<'patient' | 'doctor' | 'pharmacist' | 'admin'>
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard',       label: 'Dashboard',       icon: LayoutDashboard, roles: ['patient', 'doctor', 'pharmacist', 'admin'] },
  { to: '/doctors',         label: 'Find a Doctor',   icon: Search,          roles: ['patient'] },
  { to: '/symptom-checker', label: 'Symptom Checker', icon: Stethoscope,     roles: ['patient'] },
  { to: '/records',         label: 'Medical Records', icon: FileText,        roles: ['patient', 'doctor'] },
]

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const { unreadCount, clearUnread } = useSocket()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const visibleItems = NAV_ITEMS.filter((item) => user && item.roles.includes(user.role))

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-surface font-body">
      {/* ── Top bar ───────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border-soft bg-surface-raised px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            className="rounded-lg p-2 text-ink-soft hover:bg-surface lg:hidden"
            onClick={() => setMobileOpen((o) => !o)}
            aria-label="Toggle navigation"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <a href="/dashboard" className="flex items-center gap-2">
            <PulseLogo className="h-7 w-7 text-brand-teal" />
            <span className="font-display text-lg font-semibold text-brand-ink">MediConnect</span>
          </a>
        </div>

        <div className="flex items-center gap-3">
          <button
            className="relative rounded-lg p-2 text-ink-soft hover:bg-surface"
            onClick={clearUnread}
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-brand-coral font-mono text-[10px] font-semibold text-white">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
          <div className="hidden items-center gap-2 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-teal-tint font-display text-sm font-semibold text-brand-teal-deep">
              {user?.full_name?.charAt(0) ?? '?'}
            </div>
            <div className="leading-tight">
              <p className="font-body text-sm font-medium text-ink">{user?.full_name}</p>
              <p className="font-mono text-xs capitalize text-ink-faint">{user?.role}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="rounded-lg p-2 text-ink-soft hover:bg-brand-coral-tint hover:text-brand-coral" aria-label="Log out">
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl">
        {/* ── Sidebar ─────────────────────────────────────────── */}
        <aside
          className={clsx(
            'fixed inset-y-0 left-0 top-16 z-20 w-64 transform border-r border-border-soft bg-surface-raised p-4 transition-transform lg:static lg:translate-x-0',
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <nav className="flex flex-col gap-1">
            {visibleItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 font-body text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-brand-teal-tint text-brand-teal-deep'
                      : 'text-ink-soft hover:bg-surface hover:text-ink'
                  )
                }
              >
                <Icon className="h-4.5 w-4.5" strokeWidth={1.75} />
                {label}
              </NavLink>
            ))}
          </nav>

          {/* System status footer — quiet nod to the monitoring stack */}
          <div className="mt-8 flex items-center gap-2 rounded-lg bg-surface px-3 py-2.5">
            <Activity className="h-3.5 w-3.5 text-emerald-600" />
            <span className="font-mono text-xs text-ink-faint">All systems operational</span>
          </div>
        </aside>

        {/* ── Page content ───────────────────────────────────── */}
        <main className="min-h-[calc(100vh-4rem)] flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

/** The pulse-line mark — reused from the Landing hero as the
 *  product's compact logomark (see Landing.tsx for full context). */
function PulseLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="15" stroke="currentColor" strokeWidth="1.5" opacity="0.25" />
      <path
        d="M4 16h5l2.5-7 4 14 3-9 2 4h7.5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export { PulseLogo }
