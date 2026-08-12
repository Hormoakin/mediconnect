// ══════════════════════════════════════════════════════════════
// frontend/src/pages/admin/AdminDashboardEnhanced.tsx
// ══════════════════════════════════════════════════════════════
import { useState, useEffect } from 'react'
import { Users, UserPlus, Stethoscope, Calendar, BarChart2, Trash2, Edit2, ToggleLeft, ToggleRight, RefreshCw } from 'lucide-react'
import { api } from '../../services/api'
import LoadingSpinner from '../../components/common/LoadingSpinner'

type AdminTab = 'overview' | 'users' | 'doctors' | 'appointments' | 'reports'

interface User { id: number; full_name: string; email: string; role: string; is_active: boolean; phone: string }
interface Doctor { id: number; user_full_name: string; speciality: string; hospital_name: string; rating: string; is_available: boolean; consultation_fee: string }
interface Appointment { id: number; patient_name: string; doctor_name: string; scheduled_at: string; status: string; reason: string }

const ROLES = ['patient', 'doctor', 'pharmacist', 'receptionist', 'admin']
const STATUSES = ['pending', 'confirmed', 'completed', 'cancelled', 'no_show']

const roleBadge = (role: string) => {
  const map: Record<string, string> = {
    patient: 'bg-teal-100 text-teal-700', doctor: 'bg-blue-100 text-blue-700',
    pharmacist: 'bg-green-100 text-green-700', receptionist: 'bg-purple-100 text-purple-700',
    admin: 'bg-amber-100 text-amber-700',
  }
  return map[role] || 'bg-gray-100 text-gray-700'
}

export default function AdminDashboardEnhanced() {
  const [tab, setTab]         = useState<AdminTab>('overview')
  const [stats, setStats]     = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Users state
  const [users, setUsers]           = useState<User[]>([])
  const [userRole, setUserRole]     = useState('')
  const [userSearch, setUserSearch] = useState('')
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [newUser, setNewUser]       = useState({ full_name: '', email: '', phone: '', role: 'patient', password: '' })

  // Doctors state
  const [doctors, setDoctors]       = useState<Doctor[]>([])
  const [loadingDoctors, setLoadingDoctors] = useState(false)
  const [editingDoctor, setEditingDoctor]   = useState<Doctor | null>(null)

  // Appointments state
  const [appointments, setAppointments]     = useState<Appointment[]>([])
  const [apptStatus, setApptStatus]         = useState('')
  const [apptDate, setApptDate]             = useState('')
  const [loadingAppts, setLoadingAppts]     = useState(false)

  // Reports state
  const [reportType, setReportType] = useState('summary')
  const [reportData, setReportData] = useState<any>(null)
  const [reportFrom, setReportFrom] = useState(() => {
    const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().split('T')[0]
  })
  const [reportTo, setReportTo]     = useState(() => new Date().toISOString().split('T')[0])

  useEffect(() => {
    api.get('/admin/stats/').then(r => { setStats(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  // ── Users ────────────────────────────────────────────────
  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      const { data } = await api.get('/admin/users/', { params: { role: userRole, search: userSearch } })
      setUsers(data.results || [])
    } finally { setLoadingUsers(false) }
  }

  const toggleUserActive = async (userId: number) => {
    await api.patch(`/admin/users/${userId}/toggle-active/`)
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !u.is_active } : u))
  }

  const deleteUser = async (userId: number, name: string) => {
    if (!confirm(`Permanently delete ${name}? This cannot be undone.`)) return
    await api.delete(`/admin/users/${userId}/`)
    setUsers(prev => prev.filter(u => u.id !== userId))
  }

  const resetPassword = async (userId: number, email: string) => {
    await api.patch(`/admin/users/${userId}/reset-password/`)
    alert(`Password reset email sent to ${email}`)
  }

  const createUser = async () => {
    try {
      await api.post('/admin/users/', newUser)
      alert(`User ${newUser.full_name} created successfully.`)
      setShowCreateUser(false)
      setNewUser({ full_name: '', email: '', phone: '', role: 'patient', password: '' })
      fetchUsers()
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to create user.')
    }
  }

  // ── Doctors ──────────────────────────────────────────────
  const fetchDoctors = async () => {
    setLoadingDoctors(true)
    try {
      const { data } = await api.get('/admin/doctors/')
      setDoctors(data.results || [])
    } finally { setLoadingDoctors(false) }
  }

  const updateDoctor = async (doctorId: number, fields: object) => {
    await api.patch(`/admin/doctors/${doctorId}/`, fields)
    setDoctors(prev => prev.map(d => d.id === doctorId ? { ...d, ...fields } : d))
    setEditingDoctor(null)
  }

  const deleteDoctor = async (doctorId: number, name: string) => {
    if (!confirm(`Remove Dr. ${name}'s doctor profile? Their user account remains.`)) return
    await api.delete(`/admin/doctors/${doctorId}/`)
    setDoctors(prev => prev.filter(d => d.id !== doctorId))
  }

  // ── Appointments ─────────────────────────────────────────
  const fetchAppointments = async () => {
    setLoadingAppts(true)
    try {
      const { data } = await api.get('/admin/appointments/', { params: { status: apptStatus, date: apptDate } })
      setAppointments(data.results || [])
    } finally { setLoadingAppts(false) }
  }

  const cancelAppointment = async (apptId: number) => {
    if (!confirm('Cancel this appointment?')) return
    await api.delete(`/admin/appointments/${apptId}/`)
    setAppointments(prev => prev.map(a => a.id === apptId ? { ...a, status: 'cancelled' } : a))
  }

  // ── Reports ──────────────────────────────────────────────
  const generateReport = async () => {
    try {
      const { data } = await api.get('/admin/reports/', { params: { type: reportType, from: reportFrom, to: reportTo } })
      setReportData(data)
    } catch { alert('Report generation failed.') }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">System Administration</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">Full control over users, doctors, appointments and reports.</p>
      </div>

      {/* Overview stats */}
      {!loading && stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: 'Total Users', value: stats.users?.total || 0, color: 'text-teal-700', icon: Users },
            { label: 'Appointments Today', value: stats.appointments?.total || 0, color: 'text-amber-600', icon: Calendar },
            { label: 'Prescriptions (30d)', value: stats.prescriptions?.issued || 0, color: 'text-purple-600', icon: Stethoscope },
            { label: 'No-show Rate', value: `${stats.appointments?.no_show_rate_pct || 0}%`, color: 'text-coral-600', icon: BarChart2 },
          ].map(item => (
            <div key={item.label} className="card">
              <item.icon className={`h-5 w-5 ${item.color} mb-2`} />
              <p className={`font-display text-3xl font-semibold ${item.color}`}>{item.value}</p>
              <p className="font-body text-sm text-ink-soft">{item.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-border-soft overflow-x-auto">
        {(['overview', 'users', 'doctors', 'appointments', 'reports'] as AdminTab[]).map(t => (
          <button key={t} onClick={() => {
            setTab(t)
            if (t === 'users' && users.length === 0) fetchUsers()
            if (t === 'doctors' && doctors.length === 0) fetchDoctors()
            if (t === 'appointments' && appointments.length === 0) fetchAppointments()
          }}
            className={`px-4 py-2 font-body text-sm capitalize whitespace-nowrap transition-colors
              ${tab === t ? 'border-b-2 border-teal-700 text-teal-700 font-semibold' : 'text-ink-soft hover:text-ink'}`}>
            {t === 'appointments' ? 'Appointments' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* ── USERS TAB ─────────────────────────────────────── */}
      {tab === 'users' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <input className="input-field" placeholder="Search name or email..." value={userSearch}
              onChange={e => setUserSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && fetchUsers()} />
            <select className="input-field" value={userRole} onChange={e => setUserRole(e.target.value)}>
              <option value="">All roles</option>
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <button onClick={fetchUsers} className="btn-primary">Search</button>
            <button onClick={() => setShowCreateUser(true)} className="btn-secondary flex items-center gap-1">
              <UserPlus className="h-4 w-4" /> New User
            </button>
          </div>

          {/* Create user form */}
          {showCreateUser && (
            <div className="card border-2 border-teal-200 space-y-3">
              <h3 className="font-display text-sm font-semibold text-teal-700">Create New User</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <input className="input-field" placeholder="Full Name *" value={newUser.full_name}
                  onChange={e => setNewUser(p => ({ ...p, full_name: e.target.value }))} />
                <input type="email" className="input-field" placeholder="Email *" value={newUser.email}
                  onChange={e => setNewUser(p => ({ ...p, email: e.target.value }))} />
                <input className="input-field" placeholder="Phone" value={newUser.phone}
                  onChange={e => setNewUser(p => ({ ...p, phone: e.target.value }))} />
                <select className="input-field" value={newUser.role}
                  onChange={e => setNewUser(p => ({ ...p, role: e.target.value }))}>
                  {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
                <input className="input-field" placeholder="Password (leave blank for auto)" value={newUser.password}
                  onChange={e => setNewUser(p => ({ ...p, password: e.target.value }))} />
              </div>
              <div className="flex gap-2">
                <button onClick={createUser} className="btn-primary">Create User</button>
                <button onClick={() => setShowCreateUser(false)} className="btn-secondary">Cancel</button>
              </div>
            </div>
          )}

          {loadingUsers ? <LoadingSpinner /> : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr className="border-b border-border-soft">
                  {['Name', 'Email', 'Role', 'Status', 'Actions'].map(h => (
                    <th key={h} className="pb-3 text-left font-body text-xs font-semibold text-ink-faint">{h}</th>
                  ))}
                </tr></thead>
                <tbody className="divide-y divide-border-soft">
                  {users.map(user => (
                    <tr key={user.id} className="hover:bg-surface transition-colors">
                      <td className="py-3 pr-4">
                        <p className="font-body text-sm font-medium text-ink">{user.full_name}</p>
                        <p className="font-mono text-xs text-ink-faint">{user.phone}</p>
                      </td>
                      <td className="py-3 pr-4 font-body text-sm text-ink-soft">{user.email}</td>
                      <td className="py-3 pr-4">
                        <span className={`rounded-full px-2 py-0.5 font-body text-xs font-medium ${roleBadge(user.role)}`}>{user.role}</span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`font-body text-xs font-medium ${user.is_active ? 'text-green-600' : 'text-red-500'}`}>
                          {user.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <button onClick={() => toggleUserActive(user.id)} title={user.is_active ? 'Suspend' : 'Activate'}>
                            {user.is_active
                              ? <ToggleRight className="h-4 w-4 text-green-500 hover:text-amber-500" />
                              : <ToggleLeft className="h-4 w-4 text-gray-400 hover:text-green-500" />}
                          </button>
                          <button onClick={() => resetPassword(user.id, user.email)} title="Reset password">
                            <RefreshCw className="h-4 w-4 text-ink-faint hover:text-blue-500" />
                          </button>
                          <button onClick={() => deleteUser(user.id, user.full_name)} title="Delete user">
                            <Trash2 className="h-4 w-4 text-ink-faint hover:text-red-500" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && (
                <p className="py-8 text-center font-body text-sm text-ink-faint">No users found. Adjust your search filters.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── DOCTORS TAB ───────────────────────────────────── */}
      {tab === 'doctors' && (
        <div className="space-y-4">
          <button onClick={fetchDoctors} className="btn-secondary flex items-center gap-1">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          {loadingDoctors ? <LoadingSpinner /> : (
            <div className="grid gap-4 sm:grid-cols-2">
              {doctors.map(doc => (
                <div key={doc.id} className="card space-y-2">
                  {editingDoctor?.id === doc.id ? (
                    <div className="space-y-2">
                      <input className="input-field w-full" placeholder="Speciality"
                        defaultValue={doc.speciality}
                        onChange={e => setEditingDoctor(prev => prev ? { ...prev, speciality: e.target.value } : null)} />
                      <input className="input-field w-full" placeholder="Hospital"
                        defaultValue={doc.hospital_name}
                        onChange={e => setEditingDoctor(prev => prev ? { ...prev, hospital_name: e.target.value } : null)} />
                      <input className="input-field w-full" placeholder="Consultation Fee"
                        defaultValue={doc.consultation_fee}
                        onChange={e => setEditingDoctor(prev => prev ? { ...prev, consultation_fee: e.target.value } : null)} />
                      <div className="flex gap-2">
                        <button onClick={() => updateDoctor(doc.id, { speciality: editingDoctor.speciality, hospital_name: editingDoctor.hospital_name, consultation_fee: editingDoctor.consultation_fee })} className="btn-primary text-sm !px-3 !py-1">Save</button>
                        <button onClick={() => setEditingDoctor(null)} className="btn-secondary text-sm !px-3 !py-1">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-display text-sm font-semibold text-ink">Dr. {doc.user_full_name}</p>
                          <p className="font-body text-xs text-teal-700">{doc.speciality}</p>
                          <p className="font-body text-xs text-ink-faint">{doc.hospital_name}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => setEditingDoctor(doc)} title="Edit">
                            <Edit2 className="h-4 w-4 text-ink-faint hover:text-blue-500" />
                          </button>
                          <button onClick={() => deleteDoctor(doc.id, doc.user_full_name)} title="Remove profile">
                            <Trash2 className="h-4 w-4 text-ink-faint hover:text-red-500" />
                          </button>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm text-ink">₦{parseFloat(doc.consultation_fee).toLocaleString()}</span>
                        <span className="font-body text-xs text-amber-600">★ {doc.rating}</span>
                        <span className={`font-body text-xs ${doc.is_available ? 'text-green-600' : 'text-gray-400'}`}>
                          {doc.is_available ? 'Available' : 'Unavailable'}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── APPOINTMENTS TAB ──────────────────────────────── */}
      {tab === 'appointments' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <select className="input-field" value={apptStatus} onChange={e => setApptStatus(e.target.value)}>
              <option value="">All statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <input type="date" className="input-field" value={apptDate} onChange={e => setApptDate(e.target.value)} />
            <button onClick={fetchAppointments} className="btn-primary">Filter</button>
          </div>
          {loadingAppts ? <LoadingSpinner /> : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr className="border-b border-border-soft">
                  {['Patient', 'Doctor', 'Date & Time', 'Reason', 'Status', 'Action'].map(h => (
                    <th key={h} className="pb-3 text-left font-body text-xs font-semibold text-ink-faint">{h}</th>
                  ))}
                </tr></thead>
                <tbody className="divide-y divide-border-soft">
                  {appointments.map(appt => (
                    <tr key={appt.id} className="hover:bg-surface">
                      <td className="py-3 pr-4 font-body text-sm text-ink">{appt.patient_name}</td>
                      <td className="py-3 pr-4 font-body text-sm text-ink-soft">Dr. {appt.doctor_name}</td>
                      <td className="py-3 pr-4 font-mono text-xs text-ink">
                        {new Date(appt.scheduled_at).toLocaleString('en-NG', { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td className="py-3 pr-4 font-body text-xs text-ink-faint max-w-xs truncate">{appt.reason}</td>
                      <td className="py-3 pr-4">
                        <span className={`text-xs font-medium ${appt.status === 'completed' ? 'text-teal-700' : appt.status === 'cancelled' ? 'text-red-500' : appt.status === 'confirmed' ? 'text-green-600' : 'text-amber-600'}`}>
                          {appt.status}
                        </span>
                      </td>
                      <td className="py-3">
                        {!['completed', 'cancelled'].includes(appt.status) && (
                          <button onClick={() => cancelAppointment(appt.id)}>
                            <Trash2 className="h-4 w-4 text-ink-faint hover:text-red-500" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {appointments.length === 0 && (
                <p className="py-8 text-center font-body text-sm text-ink-faint">No appointments found for the selected filters.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── REPORTS TAB ───────────────────────────────────── */}
      {tab === 'reports' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3 items-end">
            <div>
              <label className="font-body text-xs text-ink-faint">Report Type</label>
              <select className="input-field mt-1" value={reportType} onChange={e => setReportType(e.target.value)}>
                {['summary', 'appointments', 'users', 'prescriptions'].map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-body text-xs text-ink-faint">From</label>
              <input type="date" className="input-field mt-1" value={reportFrom} onChange={e => setReportFrom(e.target.value)} />
            </div>
            <div>
              <label className="font-body text-xs text-ink-faint">To</label>
              <input type="date" className="input-field mt-1" value={reportTo} onChange={e => setReportTo(e.target.value)} />
            </div>
            <button onClick={generateReport} className="btn-primary">Generate Report</button>
          </div>

          {reportData && (
            <div className="card space-y-4">
              <h3 className="font-display text-sm font-semibold text-teal-700 capitalize">{reportType} Report</h3>
              <pre className="overflow-x-auto rounded-lg bg-surface p-4 font-mono text-xs text-ink-soft">
                {JSON.stringify(reportData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
