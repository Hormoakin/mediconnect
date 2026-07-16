// ══════════════════════════════════════════════════════════════
// frontend/src/pages/patient/FindDoctors.tsx
// ══════════════════════════════════════════════════════════════
import { useState, useCallback } from 'react'
import { Search, Star, MapPin, ChevronDown } from 'lucide-react'
import type { DoctorProfile } from '../../types/user'
import BookAppointmentModal from '../../components/forms/BookAppointmentModal'

const SPECIALITIES = [
  'General Practitioner','Cardiologist','Dermatologist','Neurologist',
  'Gynaecologist','Paediatrician','Ophthalmologist','Orthopaedic Surgeon',
  'Psychiatrist','Urologist',
]

export function FindDoctors() {
  const [search, setSearch] = useState('')
  const [speciality, setSpeciality] = useState('')
  const [doctors, setDoctors] = useState<DoctorProfile[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [bookingDoctor, setBookingDoctor] = useState<DoctorProfile | null>(null)

  const handleSearch = useCallback(async () => {
    setLoading(true)
    setSearched(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (speciality) params.set('speciality', speciality)
      params.set('ordering', '-rating')
      const { data } = await api.get(`/doctors/?${params}`)
      setDoctors(data.results ?? data)
    } finally {
      setLoading(false)
    }
  }, [search, speciality])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">Find a Doctor</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">Search by name, speciality, or hospital.</p>
      </div>

      {/* Search bar */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
          <input
            className="input-field pl-10"
            placeholder="Dr. Adeyemi, Lagos General…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <div className="relative">
          <select
            className="input-field appearance-none pr-8"
            value={speciality}
            onChange={e => setSpeciality(e.target.value)}
          >
            <option value="">All specialities</option>
            {SPECIALITIES.map(s => <option key={s}>{s}</option>)}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
        </div>
        <button onClick={handleSearch} disabled={loading} className="btn-primary">
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>

      {/* Results */}
      {!searched && (
        <p className="font-body text-sm text-ink-faint text-center py-10">Search above to find available doctors.</p>
      )}
      {searched && doctors.length === 0 && !loading && (
        <EmptyState icon={Search} title="No doctors found" description="Try a different name or speciality." />
      )}
      {doctors.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {doctors.map(doc => (
            <div key={doc.id} className="card hover:shadow-card-hover transition-shadow">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-brand-teal-tint font-display text-lg font-semibold text-brand-teal-deep">
                  {doc.user_full_name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-display text-base font-semibold text-ink truncate">Dr. {doc.user_full_name}</p>
                  <p className="font-body text-sm text-brand-teal">{doc.speciality}</p>
                  {doc.hospital_name && (
                    <div className="mt-1 flex items-center gap-1 font-body text-xs text-ink-faint">
                      <MapPin className="h-3 w-3" /> {doc.hospital_name}
                    </div>
                  )}
                  <div className="mt-2 flex items-center gap-3">
                    <span className="flex items-center gap-0.5 font-mono text-xs text-amber-600">
                      <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                      {parseFloat(doc.rating).toFixed(1)} ({doc.total_reviews})
                    </span>
                    <span className="font-mono text-xs text-ink-faint">
                      {doc.years_experience} yr{doc.years_experience !== 1 ? 's' : ''} exp
                    </span>
                    <span className={`badge ${doc.is_available ? 'badge-confirmed' : 'badge-cancelled'}`}>
                      {doc.is_available ? 'Available' : 'Unavailable'}
                    </span>
                  </div>
                </div>
              </div>
              {doc.bio && <p className="mt-3 font-body text-xs leading-relaxed text-ink-soft line-clamp-2">{doc.bio}</p>}
              <div className="mt-4 flex items-center justify-between">
                <span className="font-mono text-sm font-medium text-ink">
                  ₦{parseFloat(doc.consultation_fee).toLocaleString()}
                </span>
                <button
                  onClick={() => setBookingDoctor(doc)}
                  disabled={!doc.is_available}
                  className="btn-primary !py-1.5 !px-4 text-sm"
                >
                  Book appointment
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {bookingDoctor && (
        <BookAppointmentModal
          doctor={bookingDoctor}
          onClose={() => setBookingDoctor(null)}
          onBooked={() => { setBookingDoctor(null) }}
        />
      )}
    </div>
  )
}
export default FindDoctors
