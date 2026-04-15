import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  Package, ShoppingBag, Calendar, BookOpen, Plus, Eye,
  CheckCircle2, XCircle, RotateCcw, Clock, Star, ChevronRight
} from 'lucide-react'
import { rentalsApi, ordersApi, listingsApi, servicesApi } from '../api/client'
import useAuthStore from '../store/authStore'
import { formatDistanceToNow, format } from 'date-fns'
import clsx from 'clsx'

const STATUS_COLORS = {
  PENDING:           'badge-yellow',
  APPROVED:          'badge-blue',
  ACTIVE:            'badge-green',
  RETURNED:          'badge-ink',
  CANCELLED:         'bg-red-100 text-red-600 badge',
  COMPLETED:         'badge-green',
  PAID:              'badge-blue',
  MEETUP_SCHEDULED:  'badge-blue',
  CONFIRMED:         'badge-blue',
  DISPUTED:          'bg-red-100 text-red-600 badge',
}

const TABS = [
  { id: 'my-listings',  label: 'My Listings',  icon: BookOpen },
  { id: 'rentals',      label: 'Renting',       icon: Package },
  { id: 'lendings',     label: 'Lending Out',   icon: RotateCcw },
  { id: 'orders',       label: 'My Orders',     icon: ShoppingBag },
  { id: 'sales',        label: 'My Sales',      icon: ShoppingBag },
  { id: 'bookings',     label: 'Bookings',      icon: Calendar },
]

// ── Sub-components ─────────────────────────────────────────

function RentalCard({ rental, isOwner, onApprove, onReject, onReturn, onCancel }) {
  const listing = rental.listing
  const primaryImg = listing?.primary_image

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
        <p className="text-sm font-display font-bold text-brand-orange mt-1">${rental.total_price}</p>

        {/* Actions */}
        <div className="flex gap-2 mt-3 flex-wrap">
          {isOwner && rental.status === 'PENDING' && (
            <>
              <button onClick={() => onApprove(rental.id)}
                className="btn-primary btn-sm text-xs py-1.5 gap-1">
                <CheckCircle2 size={14} /> Approve
              </button>
              <button onClick={() => onReject(rental.id)}
                className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-display font-semibold hover:bg-red-100 transition-colors">
                <XCircle size={14} /> Decline
              </button>
            </>
          )}
          {isOwner && rental.status === 'ACTIVE' && (
            <button onClick={() => onReturn(rental.id)}
              className="btn-secondary btn-sm text-xs py-1.5 gap-1">
              <RotateCcw size={14} /> Mark Returned
            </button>
          )}
          {!isOwner && rental.status === 'PENDING' && (
            <button onClick={() => onCancel(rental.id)}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-display font-semibold hover:bg-red-100 transition-colors">
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function OrderCard({ order, isSeller }) {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const primaryImg = order.listing?.primary_image

  const completeMutation = useMutation({
    mutationFn: () => ordersApi.complete(order.id),
    onSuccess: () => { toast.success('Order completed!'); qc.invalidateQueries(['orders']) },
  })

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
        <p className="text-xs text-brand-ink/50 font-body mt-0.5">
          {isSeller ? `Buyer: ${order.buyer?.first_name}` : `Seller: ${order.seller?.first_name}`}
        </p>
        <p className="text-sm font-display font-bold text-brand-orange mt-1">${order.total_amount}</p>
        {order.meetup_location && (
          <p className="text-xs text-brand-ink/40 font-mono mt-0.5">📍 {order.meetup_location}</p>
        )}
        {!isSeller && order.status === 'MEETUP_SCHEDULED' && (
          <button onClick={() => completeMutation.mutate()}
            className="btn-primary btn-sm text-xs py-1.5 gap-1 mt-3">
            <CheckCircle2 size={14} /> Confirm Receipt
          </button>
        )}
      </div>
    </div>
  )
}

function ListingRow({ listing }) {
  return (
    <div className="card p-4 flex items-center gap-4">
      <div className="w-12 h-12 rounded-lg overflow-hidden bg-black/5 flex-shrink-0">
        {listing.images?.[0]?.url
          ? <img src={listing.images[0].url} alt="" className="w-full h-full object-cover" />
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

// ── Main dashboard ──────────────────────────────────────────

export default function DashboardPage() {
  const params = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState(params.tab || 'my-listings')

  const { data: listings } = useQuery({
    queryKey: ['my-listings'],
    queryFn: () => listingsApi.getMine().then((r) => r.data),
    enabled: activeTab === 'my-listings',
  })

  const { data: rentals } = useQuery({
    queryKey: ['my-rentals'],
    queryFn: () => rentalsApi.getMyRentals().then((r) => r.data),
    enabled: activeTab === 'rentals',
  })

  const { data: lendings } = useQuery({
    queryKey: ['my-lendings'],
    queryFn: () => rentalsApi.getMyLendings().then((r) => r.data),
    enabled: activeTab === 'lendings',
  })

  const { data: orders } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => ordersApi.getMyOrders().then((r) => r.data),
    enabled: activeTab === 'orders',
  })

  const { data: sales } = useQuery({
    queryKey: ['my-sales'],
    queryFn: () => ordersApi.getMySales().then((r) => r.data),
    enabled: activeTab === 'sales',
  })

  const { data: bookings } = useQuery({
    queryKey: ['my-bookings'],
    queryFn: () => servicesApi.getMyBookings().then((r) => r.data),
    enabled: activeTab === 'bookings',
  })

  const rentalMutation = (action) => useMutation({
    mutationFn: (id) => rentalsApi.respond(id, action),
    onSuccess: () => { toast.success(`Rental ${action}d!`); qc.invalidateQueries(['my-lendings']) },
  })

  const approveRental = useMutation({
    mutationFn: (id) => rentalsApi.respond(id, 'approve'),
    onSuccess: () => { toast.success('Rental approved!'); qc.invalidateQueries(['my-lendings']) },
  })
  const rejectRental = useMutation({
    mutationFn: (id) => rentalsApi.respond(id, 'reject'),
    onSuccess: () => { toast.success('Rental declined.'); qc.invalidateQueries(['my-lendings']) },
  })
  const returnRental = useMutation({
    mutationFn: (id) => rentalsApi.markReturned(id, { return_deposit: true }),
    onSuccess: () => { toast.success('Marked as returned!'); qc.invalidateQueries(['my-lendings']) },
  })
  const cancelRental = useMutation({
    mutationFn: (id) => rentalsApi.cancel(id),
    onSuccess: () => { toast.success('Rental cancelled.'); qc.invalidateQueries(['my-rentals']) },
  })

  const switchTab = (tab) => {
    setActiveTab(tab)
    navigate(`/dashboard/${tab}`, { replace: true })
  }

  return (
    <div className="page-container py-10">

      {/* Header */}
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

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1 mb-6 border-b border-black/5">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id}
            onClick={() => switchTab(id)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2.5 rounded-t-lg font-display font-semibold text-sm whitespace-nowrap transition-all',
              activeTab === id
                ? 'bg-brand-orange text-white'
                : 'text-brand-ink/50 hover:text-brand-ink hover:bg-black/5'
            )}>
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="space-y-3 animate-fade-in">

        {activeTab === 'my-listings' && (
          <>
            {!listings?.length
              ? <EmptyState icon="📦" title="No listings yet" action={{ label: 'Post your first listing', to: '/create' }} />
              : listings.map((l) => <ListingRow key={l.id} listing={l} />)
            }
          </>
        )}

        {activeTab === 'rentals' && (
          <>
            {!rentals?.length
              ? <EmptyState icon="🚲" title="No rentals yet" action={{ label: 'Browse rentals', to: '/browse?type=RENTAL' }} />
              : rentals.map((r) => (
                  <RentalCard key={r.id} rental={r} isOwner={false}
                    onCancel={cancelRental.mutate} />
                ))
            }
          </>
        )}

        {activeTab === 'lendings' && (
          <>
            {!lendings?.length
              ? <EmptyState icon="🤝" title="No lending activity yet" action={{ label: 'Post a rental listing', to: '/create' }} />
              : lendings.map((r) => (
                  <RentalCard key={r.id} rental={r} isOwner={true}
                    onApprove={approveRental.mutate}
                    onReject={rejectRental.mutate}
                    onReturn={returnRental.mutate} />
                ))
            }
          </>
        )}

        {activeTab === 'orders' && (
          <>
            {!orders?.length
              ? <EmptyState icon="🛒" title="No orders yet" action={{ label: 'Browse marketplace', to: '/browse?type=SALE' }} />
              : orders.map((o) => <OrderCard key={o.id} order={o} isSeller={false} />)
            }
          </>
        )}

        {activeTab === 'sales' && (
          <>
            {!sales?.length
              ? <EmptyState icon="💰" title="No sales yet" action={{ label: 'Post something for sale', to: '/create' }} />
              : sales.map((o) => <OrderCard key={o.id} order={o} isSeller={true} />)
            }
          </>
        )}

        {activeTab === 'bookings' && (
          <>
            {!bookings?.length
              ? <EmptyState icon="📅" title="No bookings yet" action={{ label: 'Browse services', to: '/browse?type=SERVICE' }} />
              : bookings.map((b) => (
                  <div key={b.id} className="card p-4">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-display font-semibold text-sm">{b.listing?.title}</p>
                      <span className={STATUS_COLORS[b.status] || 'badge-ink'}>{b.status}</span>
                    </div>
                    <p className="text-xs text-brand-ink/50 font-mono mt-1">
                      {format(new Date(b.scheduled_at), 'MMM d, yyyy · h:mm a')} · {b.duration_hours}h
                    </p>
                    <p className="text-sm font-bold text-brand-orange mt-1">${b.total_amount}</p>
                  </div>
                ))
            }
          </>
        )}
      </div>
    </div>
  )
}

function EmptyState({ icon, title, action }) {
  return (
    <div className="text-center py-16 animate-fade-in">
      <p className="text-5xl mb-4">{icon}</p>
      <h3 className="font-display font-bold text-lg text-brand-ink mb-4">{title}</h3>
      {action && (
        <Link to={action.to} className="btn-primary inline-flex">
          {action.label} <ChevronRight size={16} />
        </Link>
      )}
    </div>
  )
}