import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Heart, MapPin, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react'
import { listingsApi, rentalsApi, ordersApi, servicesApi } from '../api/client'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import clsx from 'clsx'

const API_BASE_URL = 'http://localhost:8000/api/v1'
const BACKEND_BASE_URL = 'http://localhost:8000'

const getMediaUrl = (url) => {
  if (!url) return null
  return url.startsWith('/static/') ? `${BACKEND_BASE_URL}${url}` : url
}

export default function ListingPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()

  const [photoIdx, setPhotoIdx] = useState(0)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [startingConversation, setStartingConversation] = useState(false)

  const [scheduledAt, setScheduledAt] = useState('')
  const [durationHours, setDurationHours] = useState(1)
  const [bookingNotes, setBookingNotes] = useState('')

  const { data: listing, isLoading } = useQuery({
    queryKey: ['listing', id],
    queryFn: () => listingsApi.getOne(id).then((r) => r.data),
  })

  const orderMutation = useMutation({
    mutationFn: () => ordersApi.create({ listing_id: id, quantity: 1 }),
    onSuccess: () => {
      toast.success('Order placed!')
      navigate('/dashboard/orders')
    },
  })

  const rentalMutation = useMutation({
    mutationFn: () =>
      rentalsApi.request({
        listing_id: id,
        start_date: startDate,
        end_date: endDate,
      }),
    onSuccess: () => {
      toast.success('Rental request sent!')
      navigate('/dashboard/rentals')
    },
  })

  const bookingMutation = useMutation({
    mutationFn: () =>
      servicesApi.createBooking({
        listing_id: id,
        scheduled_at: scheduledAt,
        duration_hours: Number(durationHours),
        notes: bookingNotes,
      }),
    onSuccess: () => {
      toast.success('Booking request sent!')
      navigate('/dashboard/bookings')
    },
  })

  const startConversation = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    if (!listing?.user?.id) {
      toast.error('Seller info is missing for this listing.')
      return
    }

    if (user?.id === listing.user.id) {
      toast.error('You cannot message yourself.')
      return
    }

    const token = localStorage.getItem('access_token')
    if (!token) {
      navigate('/login')
      return
    }

    setStartingConversation(true)
    try {
      const res = await fetch(`${API_BASE_URL}/messages/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          recipient_id: listing.user.id,
          listing_id: listing.id,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data?.detail || 'Could not open conversation.')
      }

      navigate(`/messages/${data.id}`)
    } catch (err) {
      toast.error(err.message || 'Could not start conversation.')
    } finally {
      setStartingConversation(false)
    }
  }

  const handleRentalRequest = () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (!startDate || !endDate) {
      toast.error('Please select rental dates.')
      return
    }
    rentalMutation.mutate()
  }

  const handleServiceBooking = () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (!scheduledAt) {
      toast.error('Please choose a date and time.')
      return
    }
    if (!durationHours || Number(durationHours) < 1) {
      toast.error('Please enter a valid duration.')
      return
    }
    bookingMutation.mutate()
  }

  if (isLoading) {
    return (
      <div className="page-container py-10">
        <div className="grid md:grid-cols-2 gap-10 animate-pulse">
          <div className="aspect-square bg-black/5 rounded-2xl" />
          <div className="space-y-4">
            <div className="h-8 bg-black/5 rounded w-3/4" />
            <div className="h-6 bg-black/5 rounded w-1/3" />
            <div className="h-24 bg-black/5 rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (!listing) {
    return (
      <div className="page-container py-20 text-center">
        <p className="text-4xl mb-4">😕</p>
        <h2 className="font-display font-bold text-2xl">Listing not found</h2>
        <Link to="/browse" className="btn-primary inline-flex mt-6">Browse listings</Link>
      </div>
    )
  }

  const images = listing.images || []
  const currentImage = getMediaUrl(images[photoIdx]?.url)
  const isOwner = user?.id === listing.user?.id

  const price =
    listing.type === 'RENTAL'
      ? `$${listing.rental_details?.price_per_period}/${listing.rental_details?.price_period?.toLowerCase()}`
      : listing.type === 'SERVICE'
        ? `$${listing.service_details?.price_per_hour}/hr`
        : `$${listing.sale_details?.price}`

  return (
    <div className="page-container py-10">
      <Link to="/browse" className="inline-flex items-center gap-1.5 text-brand-ink/50 hover:text-brand-ink font-body text-sm mb-6 transition-colors">
        <ChevronLeft size={16} /> Back to listings
      </Link>

      <div className="grid md:grid-cols-2 gap-10">
        <div>
          <div className="relative aspect-square rounded-2xl overflow-hidden bg-black/5">
            {currentImage ? (
              <img src={currentImage} alt={listing.title} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-6xl">
                {listing.type === 'RENTAL' ? '📦' : listing.type === 'SERVICE' ? '🎓' : '🏷️'}
              </div>
            )}

            {images.length > 1 && (
              <>
                <button
                  onClick={() => setPhotoIdx((i) => (i - 1 + images.length) % images.length)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-white rounded-full shadow flex items-center justify-center hover:scale-110 transition-transform"
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  onClick={() => setPhotoIdx((i) => (i + 1) % images.length)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-white rounded-full shadow flex items-center justify-center hover:scale-110 transition-transform"
                >
                  <ChevronRight size={18} />
                </button>
              </>
            )}
          </div>

          {images.length > 1 && (
            <div className="flex gap-2 mt-3">
              {images.map((img, i) => (
                <button
                  key={i}
                  onClick={() => setPhotoIdx(i)}
                  className={clsx(
                    'w-14 h-14 rounded-lg overflow-hidden border-2 transition-all',
                    i === photoIdx ? 'border-brand-orange' : 'border-transparent opacity-60 hover:opacity-100'
                  )}
                >
                  <img
                    src={getMediaUrl(img.url)}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-start justify-between gap-3 mb-3">
            <span className={`type-chip-${listing.type.toLowerCase()}`}>{listing.type.toLowerCase()}</span>
            <button className="w-9 h-9 border-2 border-black/10 rounded-lg flex items-center justify-center hover:border-brand-orange transition-colors">
              <Heart size={16} className="text-brand-ink/40" />
            </button>
          </div>

          <h1 className="font-display font-bold text-2xl sm:text-3xl text-brand-ink mb-2">{listing.title}</h1>
          <p className="font-display font-bold text-3xl text-brand-orange mb-4">{price}</p>

          {listing.location && (
            <div className="flex items-center gap-1.5 text-brand-ink/50 font-body text-sm mb-4">
              <MapPin size={14} />
              <span>{listing.location}</span>
            </div>
          )}

          <p className="text-brand-ink/70 font-body leading-relaxed mb-6">{listing.description}</p>

          {listing.type === 'SALE' && listing.sale_details?.condition && (
            <div className="flex items-center gap-2 mb-6">
              <span className="label mb-0">Condition:</span>
              <span className="badge-blue">{listing.sale_details.condition.replace('_', ' ')}</span>
              {listing.sale_details.is_negotiable && <span className="badge-yellow">Negotiable</span>}
            </div>
          )}

          {listing.type === 'RENTAL' && !isOwner && (
            <div className="card p-4 mb-4 space-y-3">
              <p className="font-display font-semibold text-sm text-brand-ink">Select rental dates</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label text-xs">Start date</label>
                  <input
                    type="date"
                    className="input text-sm py-2"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    min={format(new Date(), 'yyyy-MM-dd')}
                  />
                </div>
                <div>
                  <label className="label text-xs">End date</label>
                  <input
                    type="date"
                    className="input text-sm py-2"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || format(new Date(), 'yyyy-MM-dd')}
                  />
                </div>
              </div>
              {listing.rental_details?.deposit_amount > 0 && (
                <p className="text-xs text-brand-ink/40 font-mono">
                  + ${listing.rental_details.deposit_amount} deposit (refundable)
                </p>
              )}
            </div>
          )}

          {listing.type === 'SERVICE' && !isOwner && (
            <div className="card p-4 mb-4 space-y-3">
              <p className="font-display font-semibold text-sm text-brand-ink">Book this service</p>

              <div>
                <label className="label text-xs">Date & time</label>
                <input
                  type="datetime-local"
                  className="input text-sm py-2"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                />
              </div>

              <div>
                <label className="label text-xs">Duration (hours)</label>
                <input
                  type="number"
                  min={listing.service_details?.min_hours || 1}
                  max={listing.service_details?.max_hours || 12}
                  className="input text-sm py-2"
                  value={durationHours}
                  onChange={(e) => setDurationHours(e.target.value)}
                />
              </div>

              <div>
                <label className="label text-xs">Notes (optional)</label>
                <textarea
                  className="input text-sm min-h-[90px]"
                  value={bookingNotes}
                  onChange={(e) => setBookingNotes(e.target.value)}
                  placeholder="Anything the provider should know?"
                />
              </div>

              <p className="text-xs text-brand-ink/40 font-mono">
                {listing.service_details?.min_hours ? `Min ${listing.service_details.min_hours} hr` : 'Min 1 hr'}
                {listing.service_details?.max_hours ? ` · Max ${listing.service_details.max_hours} hr` : ''}
              </p>
            </div>
          )}

          {!isOwner && (
            <div className="space-y-3">
              {listing.type === 'SALE' && (
                <button
                  onClick={() => (isAuthenticated ? orderMutation.mutate() : navigate('/login'))}
                  disabled={orderMutation.isPending}
                  className="btn-primary w-full justify-center text-base py-4"
                >
                  {orderMutation.isPending ? 'Placing order...' : 'Buy now'}
                </button>
              )}

              {listing.type === 'RENTAL' && (
                <button
                  onClick={handleRentalRequest}
                  disabled={rentalMutation.isPending}
                  className="btn-primary w-full justify-center text-base py-4"
                >
                  {rentalMutation.isPending ? 'Sending request...' : 'Request rental'}
                </button>
              )}

              {listing.type === 'SERVICE' && (
                <button
                  onClick={handleServiceBooking}
                  disabled={bookingMutation.isPending}
                  className="btn-primary w-full justify-center text-base py-4"
                >
                  {bookingMutation.isPending ? 'Sending request...' : 'Book service'}
                </button>
              )}

              <button
                onClick={startConversation}
                disabled={startingConversation}
                className="btn-secondary w-full justify-center text-base py-4"
              >
                <MessageSquare size={18} />
                {startingConversation ? 'Opening...' : 'Message seller'}
              </button>
            </div>
          )}

          {isOwner && (
            <div className="card p-4 border border-brand-orange/20 bg-brand-orange/5">
              <p className="font-display font-semibold text-brand-ink mb-1">This is your listing</p>
              <p className="text-sm text-brand-ink/60">
                You can manage it from your dashboard under My Listings.
              </p>
              <Link to="/dashboard/my-listings" className="btn-secondary mt-4 inline-flex">
                Go to dashboard
              </Link>
            </div>
          )}

          <div className="mt-8 flex items-center gap-3 rounded-xl bg-black/[0.03] p-4">
            <div className="w-11 h-11 rounded-full overflow-hidden bg-brand-ink flex items-center justify-center text-white font-display font-semibold">
              {listing.user?.avatar_url ? (
                <img src={listing.user.avatar_url} alt="" className="w-full h-full object-cover" />
              ) : (
                listing.user?.first_name?.[0] || '?'
              )}
            </div>
            <div className="flex-1">
              <p className="font-display font-semibold text-sm text-brand-ink">
                {listing.user?.first_name} {listing.user?.last_name}
              </p>
              <p className="text-xs text-brand-ink/45">{listing.university}</p>
            </div>
            {listing.user?.id && (
              <Link to={`/profile/${listing.user.id}`} className="text-sm text-brand-orange font-display font-semibold">
                View profile
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}