import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  Package, ShoppingBag, Calendar, BookOpen, Plus, Eye,
  CheckCircle2, XCircle, RotateCcw, ChevronRight
} from 'lucide-react'
import { rentalsApi, ordersApi, listingsApi, servicesApi } from '../api/client'
import useAuthStore from '../store/authStore'
import { format } from 'date-fns'
import clsx from 'clsx'

const BACKEND_BASE_URL = 'http://localhost:8000'

const STATUS_COLORS = {
  PENDING: 'badge-yellow',
  APPROVED: 'badge-blue',
  ACTIVE: 'badge-green',
  RETURNED: 'badge-ink',
  CANCELLED: 'bg-red-100 text-red-600 badge',
  COMPLETED: 'badge-green',
  PAID: 'badge-blue',
  MEETUP_SCHEDULED: 'badge-blue',
  CONFIRMED: 'badge-blue',
  DISPUTED: 'bg-red-100 text-red-600 badge',
}

const TABS = [
  { id: 'my-listings', label: 'My Listings', icon: BookOpen },
  { id: 'rentals', label: 'Renting', icon: Package },
  { id: 'lendings', label: 'Lending Out', icon: RotateCcw },
  { id: 'orders', label: 'My Orders', icon: ShoppingBag },
  { id: 'sales', label: 'My Sales', icon: ShoppingBag },
  { id: 'bookings', label: 'Bookings', icon: Calendar },
]

const getMediaUrl = (url) => {
  if (!url) return null
  return url.startsWith('/static/') ? `${BACKEND_BASE_URL}${url}` : url
}

function RentalCard({ rental, isOwner, onApprove, onReject, onReturn, onCancel }) {
  const listing = rental.listing
  const primaryImg = getMediaUrl(listing?.primary_image)

  return (
    <div className="card p-4 flex gap-4">
      <div className="w-16 h-16 rounded-xl overflow-hidden bg-black/5 flex-shrink-0">
        {primaryImg
          ? <img src={primaryImg} alt="" className="w-full h-full object-cover" />
          : <div className="w-full h-full flex items-center justify-center text-2xl">📦</div>
        }
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="font-display font-semibold text-sm text-brand-ink truncate">{listing?.title}</p>
          <span className={STATUS_COLORS[rental.status] || 'badge-ink'}>{rental.status}</span>
        </div>

        <p className="text-xs text-brand-ink/50 font-mono mt-0.5">
          {format(new Date(rental.start_date), 'MMM d')} – {format(new Date(rental.end_date), 'MMM d, yyyy')}
        </p>

        {/* <p className="text-sm text-brand-ink/60 font-body mt-1">
          {isOwner
            ? `Rented by: ${rental.renter?.first_name || 'Student'}`
            : `Owner: ${rental.owner?.first_name || 'Student'}`}
        </p> */}
        <div className="flex items-center gap-2 mt-2">
  <div className="w-6 h-6 rounded-full bg-black/10 overflow-hidden flex items-center justify-center text-xs font-bold">
    {(isOwner
      ? rental.renter?.first_name?.[0]
      : rental.owner?.first_name?.[0]) || '?'}
  </div>

  <p className="text-sm text-brand-ink/70 font-body">
    {isOwner
      ? `Rented by ${rental.renter?.first_name || 'Student'}`
      : `Owned by ${rental.owner?.first_name || 'Student'}`}
  </p>
</div>

        <p className="text-sm font-display font-bold text-brand-orange mt-1">${rental.total_price}</p>

        <div className="flex gap-2 mt-3 flex-wrap">
          {isOwner && rental.status === 'PENDING' && (
            <>
              <button onClick={() => onApprove(rental.id)} className="btn-primary btn-sm text-xs py-1.5 gap-1">
                <CheckCircle2 size={14} /> Approve
              </button>
              <button
                onClick={() => onReject(rental.id)}
                className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-display font-semibold hover:bg-red-100 transition-colors"
              >
                <XCircle size={14} /> Decline
              </button>
            </>
          )}

          {isOwner && (rental.status === 'APPROVED' || rental.status === 'ACTIVE') && (
            <button onClick={() => onReturn(rental.id)} className="btn-secondary btn-sm text-xs py-1.5 gap-1">
              <RotateCcw size={14} /> Mark Returned
            </button>
          )}

          {!isOwner && (rental.status === 'PENDING' || rental.status === 'APPROVED') && (
            <button
              onClick={() => onCancel(rental.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-display font-semibold hover:bg-red-100 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function OrderCard({ order, isSeller, onScheduleMeetup, onComplete, onCancel }) {
  const primaryImg = getMediaUrl(order.listing?.primary_image)
  const [meetupLocation, setMeetupLocation] = useState(order.meetup_location || '')
  const [meetupTime, setMeetupTime] = useState(
    order.meetup_time ? new Date(order.meetup_time).toISOString().slice(0, 16) : ''
  )

  return (
    <div className="card p-4 flex gap-4">
      <div className="w-16 h-16 rounded-xl overflow-hidden bg-black/5 flex-shrink-0">
        {primaryImg
          ? <img src={primaryImg} alt="" className="w-full h-full object-cover" />
          : <div className="w-full h-full flex items-center justify-center text-2xl">🏷️</div>
        }
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="font-display font-semibold text-sm text-brand-ink truncate">{order.listing?.title}</p>
          <span className={STATUS_COLORS[order.status] || 'badge-ink'}>{order.status.replace('_', ' ')}</span>
        </div>

        <p className="text-sm text-brand-ink/60 font-body mt-1">
          {isSeller
            ? `Sold to: ${order.buyer?.first_name || 'Student'}`
            : `Sold by: ${order.seller?.first_name || 'Student'}`}
        </p>

        <p className="text-sm font-display font-bold text-brand-orange mt-1">${order.total_amount}</p>

        {order.meetup_location && (
          <p className="text-xs text-brand-ink/40 font-mono mt-0.5">
            📍 {order.meetup_location}
          </p>
        )}

        {order.meetup_time && (
          <p className="text-xs text-brand-ink/40 font-mono mt-0.5">
            🕒 {format(new Date(order.meetup_time), 'MMM d, yyyy h:mm a')}
          </p>
        )}

        <div className="flex gap-2 mt-3 flex-wrap">
          {isSeller && (order.status === 'PENDING' || order.status === 'PAID') && (
            <div className="w-full grid sm:grid-cols-[1fr_1fr_auto] gap-2 mt-1">
              <input
                className="input text-sm py-2"
                placeholder="Meetup location"
                value={meetupLocation}
                onChange={(e) => setMeetupLocation(e.target.value)}
              />
              <input
                type="datetime-local"
                className="input text-sm py-2"
                value={meetupTime}
                onChange={(e) => setMeetupTime(e.target.value)}
              />
              <button
                onClick={() => onScheduleMeetup(order.id, meetupLocation, meetupTime)}
                className="btn-primary btn-sm text-xs py-1.5"
              >
                Schedule
              </button>
            </div>
          )}

          {!isSeller && order.status === 'MEETUP_SCHEDULED' && (
            <button onClick={() => onComplete(order.id)} className="btn-primary btn-sm text-xs py-1.5 gap-1">
              <CheckCircle2 size={14} /> Confirm Receipt
            </button>
          )}

          {!isSeller && order.status === 'PENDING' && (
            <button
              onClick={() => onCancel(order.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-display font-semibold hover:bg-red-100 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function BookingCard({ booking, isProvider, onConfirm, onComplete, onCancel }) {
  const primaryImg = getMediaUrl(booking.listing?.primary_image)

  return (
    <div className="card p-4 flex gap-4">
      <div className="w-16 h-16 rounded-xl overflow-hidden bg-black/5 flex-shrink-0">
        {primaryImg
          ? <img src={primaryImg} alt="" className="w-full h-full object-cover" />
          : <div className="w-full h-full flex items-center justify-center text-2xl">🎓</div>
        }
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="font-display font-semibold text-sm text-brand-ink truncate">{booking.listing?.title}</p>
          <span className={STATUS_COLORS[booking.status] || 'badge-ink'}>{booking.status}</span>
        </div>

        <p className="text-xs text-brand-ink/50 font-body mt-0.5">
          {isProvider ? `Client: ${booking.client?.first_name}` : `Provider: ${booking.provider?.first_name}`}
        </p>

        {booking.scheduled_at && (
          <p className="text-xs text-brand-ink/40 font-mono mt-0.5">
            🗓 {format(new Date(booking.scheduled_at), 'MMM d, yyyy h:mm a')}
          </p>
        )}

        <p className="text-xs text-brand-ink/40 font-mono mt-0.5">
          ⏱ {booking.duration_hours} hr
        </p>

        <p className="text-sm font-display font-bold text-brand-orange mt-1">${booking.total_amount}</p>

        <div className="flex gap-2 mt-3 flex-wrap">
          {isProvider && booking.status === 'PENDING' && (
            <button onClick={() => onConfirm(booking.id)} className="btn-primary btn-sm text-xs py-1.5 gap-1">
              <CheckCircle2 size={14} /> Confirm
            </button>
          )}

          {!isProvider && booking.status === 'CONFIRMED' && (
            <button onClick={() => onComplete(booking.id)} className="btn-primary btn-sm text-xs py-1.5 gap-1">
              <CheckCircle2 size={14} /> Mark Complete
            </button>
          )}

          {(booking.status === 'PENDING' || booking.status === 'CONFIRMED') && (
            <button
              onClick={() => onCancel(booking.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-display font-semibold hover:bg-red-100 transition-colors"
            >
              <XCircle size={14} /> Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function ListingRow({ listing }) {
  const img = getMediaUrl(listing.images?.[0]?.url)

  return (
    <div className="card p-4 flex items-center gap-4">
      <div className="w-12 h-12 rounded-lg overflow-hidden bg-black/5 flex-shrink-0">
        {img
          ? <img src={img} alt="" className="w-full h-full object-cover" />
          : <div className="w-full h-full flex items-center justify-center">
              {listing.type === 'RENTAL' ? '📦' : listing.type === 'SERVICE' ? '🎓' : '🏷️'}
            </div>
        }
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-display font-semibold text-sm text-brand-ink truncate">{listing.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className={`type-chip-${listing.type.toLowerCase()}`}>{listing.type.toLowerCase()}</span>
          <span className="text-xs text-brand-ink/40 font-mono">{listing.view_count} views</span>
        </div>
      </div>
      <Link to={`/listings/${listing.id}`} className="text-brand-ink/40 hover:text-brand-orange transition-colors">
        <Eye size={16} />
      </Link>
    </div>
  )
}

export default function DashboardPage() {
  const params = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState(params.tab || 'my-listings')

  const { data: listings = [] } = useQuery({
    queryKey: ['my-listings'],
    queryFn: () => listingsApi.getMine().then((r) => r.data),
    enabled: activeTab === 'my-listings',
  })

  const { data: rentals = [] } = useQuery({
    queryKey: ['my-rentals'],
    queryFn: () => rentalsApi.getMyRentals().then((r) => r.data),
    enabled: activeTab === 'rentals',
  })

  const { data: lendings = [] } = useQuery({
    queryKey: ['my-lendings'],
    queryFn: () => rentalsApi.getMyLendings().then((r) => r.data),
    enabled: activeTab === 'lendings',
  })

  const { data: orders = [] } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => ordersApi.getMyOrders().then((r) => r.data),
    enabled: activeTab === 'orders',
  })

  const { data: sales = [] } = useQuery({
    queryKey: ['my-sales'],
    queryFn: () => ordersApi.getMySales().then((r) => r.data),
    enabled: activeTab === 'sales',
  })

  const { data: bookings = [] } = useQuery({
    queryKey: ['my-bookings'],
    queryFn: () => servicesApi.getMyBookings().then((r) => r.data),
    enabled: activeTab === 'bookings',
  })

  const { data: myServices = [] } = useQuery({
    queryKey: ['my-services'],
    queryFn: () => servicesApi.getMyServices().then((r) => r.data),
    enabled: activeTab === 'bookings',
  })

  const approveRental = useMutation({
    mutationFn: (id) => rentalsApi.respond(id, 'approve'),
    onSuccess: () => {
      toast.success('Rental approved!')
      qc.invalidateQueries({ queryKey: ['my-lendings'] })
    },
  })

  const rejectRental = useMutation({
    mutationFn: (id) => rentalsApi.respond(id, 'reject'),
    onSuccess: () => {
      toast.success('Rental declined.')
      qc.invalidateQueries({ queryKey: ['my-lendings'] })
    },
  })

  const returnRental = useMutation({
    mutationFn: (id) => rentalsApi.markReturned(id, { return_deposit: true }),
    onSuccess: () => {
      toast.success('Marked as returned!')
      qc.invalidateQueries({ queryKey: ['my-lendings'] })
      qc.invalidateQueries({ queryKey: ['my-rentals'] })
    },
  })

  const cancelRental = useMutation({
    mutationFn: (id) => rentalsApi.cancel(id),
    onSuccess: () => {
      toast.success('Rental cancelled.')
      qc.invalidateQueries({ queryKey: ['my-rentals'] })
      qc.invalidateQueries({ queryKey: ['my-lendings'] })
    },
  })

  const completeOrder = useMutation({
    mutationFn: (id) => ordersApi.complete(id),
    onSuccess: () => {
      toast.success('Order completed!')
      qc.invalidateQueries({ queryKey: ['my-orders'] })
      qc.invalidateQueries({ queryKey: ['my-sales'] })
    },
  })

  const cancelOrder = useMutation({
    mutationFn: (id) => ordersApi.cancel(id),
    onSuccess: () => {
      toast.success('Order cancelled.')
      qc.invalidateQueries({ queryKey: ['my-orders'] })
      qc.invalidateQueries({ queryKey: ['my-sales'] })
    },
  })

  const scheduleMeetup = useMutation({
    mutationFn: ({ id, meetup_location, meetup_time }) =>
      ordersApi.scheduleMeetup(id, { meetup_location, meetup_time }),
    onSuccess: () => {
      toast.success('Meetup scheduled!')
      qc.invalidateQueries({ queryKey: ['my-sales'] })
      qc.invalidateQueries({ queryKey: ['my-orders'] })
    },
  })

  const confirmBooking = useMutation({
    mutationFn: (id) => servicesApi.confirm(id),
    onSuccess: () => {
      toast.success('Booking confirmed!')
      qc.invalidateQueries({ queryKey: ['my-services'] })
      qc.invalidateQueries({ queryKey: ['my-bookings'] })
    },
  })

  const completeBooking = useMutation({
    mutationFn: (id) => servicesApi.complete(id),
    onSuccess: () => {
      toast.success('Booking marked complete!')
      qc.invalidateQueries({ queryKey: ['my-bookings'] })
      qc.invalidateQueries({ queryKey: ['my-services'] })
    },
  })

  const cancelBooking = useMutation({
    mutationFn: (id) => servicesApi.cancel(id),
    onSuccess: () => {
      toast.success('Booking cancelled.')
      qc.invalidateQueries({ queryKey: ['my-bookings'] })
      qc.invalidateQueries({ queryKey: ['my-services'] })
    },
  })

  const switchTab = (tab) => {
    setActiveTab(tab)
    navigate(`/dashboard/${tab}`, { replace: true })
  }

  return (
    <div className="page-container py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display font-bold text-3xl text-brand-ink">
            Hey, {user?.first_name} 👋
          </h1>
          <p className="text-brand-ink/50 font-body mt-0.5 font-mono text-sm">{user?.university}</p>
        </div>
        <Link to="/create" className="btn-primary gap-1.5">
          <Plus size={18} /> New listing
        </Link>
      </div>

      <div className="flex gap-1 overflow-x-auto pb-1 mb-6 border-b border-black/5">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => switchTab(id)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2.5 rounded-t-lg font-display font-semibold text-sm whitespace-nowrap transition-all',
              activeTab === id
                ? 'bg-brand-orange text-white'
                : 'text-brand-ink/50 hover:text-brand-ink hover:bg-black/[0.03]'
            )}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'my-listings' && (
        <div className="space-y-3">
          {listings.length ? listings.map((listing) => (
            <ListingRow key={listing.id} listing={listing} />
          )) : (
            <div className="card p-8 text-center text-brand-ink/45">
              <BookOpen className="mx-auto mb-3" size={28} />
              <p className="font-display font-semibold">No listings yet</p>
              <p className="text-sm mt-1">Create one to get started.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'rentals' && (
        <div className="space-y-3">
          {rentals.length ? rentals.map((rental) => (
            <RentalCard
              key={rental.id}
              rental={rental}
              isOwner={false}
              onCancel={(id) => cancelRental.mutate(id)}
            />
          )) : (
            <div className="card p-8 text-center text-brand-ink/45">
              <Package className="mx-auto mb-3" size={28} />
              <p className="font-display font-semibold">No rentals yet</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'lendings' && (
        <div className="space-y-3">
          {lendings.length ? lendings.map((rental) => (
            <RentalCard
              key={rental.id}
              rental={rental}
              isOwner
              onApprove={(id) => approveRental.mutate(id)}
              onReject={(id) => rejectRental.mutate(id)}
              onReturn={(id) => returnRental.mutate(id)}
            />
          )) : (
            <div className="card p-8 text-center text-brand-ink/45">
              <RotateCcw className="mx-auto mb-3" size={28} />
              <p className="font-display font-semibold">No lending activity yet</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'orders' && (
        <div className="space-y-3">
          {orders.length ? orders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              isSeller={false}
              onComplete={(id) => completeOrder.mutate(id)}
              onCancel={(id) => cancelOrder.mutate(id)}
            />
          )) : (
            <div className="card p-8 text-center text-brand-ink/45">
              <ShoppingBag className="mx-auto mb-3" size={28} />
              <p className="font-display font-semibold">No orders yet</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'sales' && (
        <div className="space-y-3">
          {sales.length ? sales.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              isSeller
              onScheduleMeetup={(id, meetup_location, meetup_time) => {
                if (!meetup_location || !meetup_time) {
                  toast.error('Please add meetup location and time.')
                  return
                }
                scheduleMeetup.mutate({ id, meetup_location, meetup_time })
              }}
            />
          )) : (
            <div className="card p-8 text-center text-brand-ink/45">
              <ShoppingBag className="mx-auto mb-3" size={28} />
              <p className="font-display font-semibold">No sales yet</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'bookings' && (
        <div className="space-y-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Calendar size={18} className="text-brand-orange" />
              <h2 className="font-display font-bold text-xl text-brand-ink">My Bookings</h2>
            </div>

            <div className="space-y-3">
              {bookings.length ? bookings.map((booking) => (
                <BookingCard
                  key={booking.id}
                  booking={booking}
                  isProvider={false}
                  onComplete={(id) => completeBooking.mutate(id)}
                  onCancel={(id) => cancelBooking.mutate(id)}
                />
              )) : (
                <div className="card p-6 text-center text-brand-ink/45">
                  <p className="font-display font-semibold">No bookings made yet</p>
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3">
              <ChevronRight size={18} className="text-brand-orange" />
              <h2 className="font-display font-bold text-xl text-brand-ink">Services I Provide</h2>
            </div>

            <div className="space-y-3">
              {myServices.length ? myServices.map((booking) => (
                <BookingCard
                  key={booking.id}
                  booking={booking}
                  isProvider
                  onConfirm={(id) => confirmBooking.mutate(id)}
                  onCancel={(id) => cancelBooking.mutate(id)}
                />
              )) : (
                <div className="card p-6 text-center text-brand-ink/45">
                  <p className="font-display font-semibold">No incoming service requests yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}