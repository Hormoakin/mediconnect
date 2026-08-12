// ══════════════════════════════════════════════════════════════
// frontend/src/App.tsx — Role-based routing
// ══════════════════════════════════════════════════════════════

import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { SocketProvider } from './contexts/SocketContext'
import ProtectedRoute from './components/common/ProtectedRoute'
import DashboardLayout from './components/layout/DashboardLayout'

import Landing from './pages/Landing'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'

import PatientDashboard from './pages/patient/PatientDashboard'
import FindDoctors from './pages/patient/FindDoctors'
import SymptomCheckerEnhanced from './pages/patient/SymptomCheckerEnhanced'

import DoctorDashboard from './pages/doctor/DoctorDashboard'
import PharmacistDashboard from './pages/pharmacist/PharmacistDashboard'
import ReceptionistDashboard from './pages/receptionist/ReceptionistDashboard'
import AdminDashboardEnhanced from './pages/admin/AdminDashboardEnhanced'

import Chat from './pages/Chat'
import MedicalRecords from './pages/MedicalRecords'

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      {/* ── Public routes ─────────────────────────────────────── */}
      <Route path="/" element={<Landing />} />

      <Route
        path="/login"
        element={
          user ? <Navigate to="/dashboard" replace /> : <Login />
        }
      />

      <Route
        path="/register"
        element={
          user ? <Navigate to="/dashboard" replace /> : <Register />
        }
      />

      {/* ── Authenticated routes ──────────────────────────────── */}
      <Route
        element={
          <ProtectedRoute>
            <SocketProvider>
              <DashboardLayout />
            </SocketProvider>
          </ProtectedRoute>
        }
      >
        {/* Role-aware dashboard */}
        <Route
          path="/dashboard"
          element={<RoleDashboardRouter />}
        />

        {/* Patient */}
        <Route
          path="/doctors"
          element={<FindDoctors />}
        />

        <Route
          path="/symptom-checker"
          element={<SymptomCheckerEnhanced />}
        />

        {/* Shared */}
        <Route
          path="/chat/:userId"
          element={<Chat />}
        />

        <Route
          path="/records"
          element={<MedicalRecords />}
        />
      </Route>

      {/* ── Catch-all ─────────────────────────────────────────── */}
      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  )
}


/**
 * Renders the correct dashboard component based on the
 * authenticated user's role (FR-01.3 — role-based access).
 */
function RoleDashboardRouter() {
  const { user } = useAuth()

  switch (user?.role) {
    case 'patient':
      return <PatientDashboard />

    case 'doctor':
      return <DoctorDashboard />

    case 'pharmacist':
      return <PharmacistDashboard />

    case 'receptionist':
      return <ReceptionistDashboard />

    case 'admin':
      return <AdminDashboardEnhanced />

    default:
      return <Navigate to="/" replace />
  }
}
