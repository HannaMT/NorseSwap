import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Heart, MapPin, Star, MessageSquare, Share2, ChevronLeft, ChevronRight, Shield, Calendar } from 'lucide-react'
import { listingsApi, rentalsApi, ordersApi } from '../api/client'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import clsx from 'clsx'

export default function ListingPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const [photoIdx, setPhotoIdx] = useState(0)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const { data: listing, isLoading } = useQuery({
    queryKey: ['listing', id],
    queryFn: () => listingsApi.getOne(id).then((r) => r.data),
  })

  const orderMutation = useMutation({
    mutationFn: () => ordersApi.create({ listing_id: id, quantity: 1 }),
    onSuccess: (res) => { toast.success('Order placed!'); navigate('/dashboard/orders') },
  })

  const rentalMutation = useMutation({
    mutationFn: () => rentalsApi.request({ listing_id: id, start_date: startDate, end_date: endDate }),
    onSuccess: () => { toast.success('Rental request sent!'); navigate('/dashboard/rentals') },
  })

  if (isLoading) return (
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

  if (!listing) return (
    <div className="page-container py-20 text-center">
      <p className="text-4xl mb-4">😕</p>
      <h2 className="font-display font-bold text-2xl">Listing not found</h2>
      <Link to="/browse" className="btn-primary inline-flex mt-6">Browse listings</Link>
    </div>
  )

  const images = listing.images || []
  const currentImage = images[photoIdx]?.url
  const isOwner = user?.id === listing.user_id

  const price =
    listing.type === 'RENTAL'  ? `$${listing.rental_details?.price_per_period}/${listing.rental_details?.price_period?.toLowerCase()}` :
    listing.type === 'SERVICE' ? `$${listing.service_details?.price_per_hour}/hr` :
    `$${listing.sale_details?.price}`

  return (
    <div className="page-container py-10">
      <Link to="/browse" className="inline-flex items-center gap-1.5 text-brand-ink/50 hover:text-brand-ink font-body text-sm mb-6 transition-colors">
        <ChevronLeft size={16} /> Back to listings
      </Link>

      <div className="grid md:grid-cols-2 gap-10">
        {/* ── Photos ───────────────────────── */}
        <div>
          <div className="relative aspect-square rounded-2xl overflow-hidden bg-black/5">
            {currentImage
              ? <img src={currentImage} alt={listing.title} className="w-full h-full object-cover" />
              : <div className="w-full h-full flex items-center justify-center text-6xl">
                  {listing.type === 'RENTAL' ? '📦' : listing.type === 'SERVICE' ? '🎓' : '🏷️'}
                </div>
            }
            {images.length > 1 && (
              <>
                <button onClick={() => setPhotoIdx((i) => (i - 1 + images.length) % images.length)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-white rounded-full shadow flex items-center justify-center hover:scale-110 transition-transform">
                  <ChevronLeft size={18} />
                </button>
                <button onClick={() => setPhotoIdx((i) => (i + 1) % images.length)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-white rounded-full shadow flex items-center justify-center hover:scale-110 transition-transform">
                  <ChevronRight size={18} />
                </button>
              </>
            )}
          </div>
          {images.length > 1 && (
            <div className="flex gap-2 mt-3">
              {images.map((img, i) => (
                <button key={i} onClick={() => setPhotoIdx(i)}
                  className={clsx('w-14 h-14 rounded-lg overflow-hidden border-2 transition-all',
                    i === photoIdx ? 'border-brand-orange' : 'border-transparent opacity-60 hover:opacity-100')}>
                  <img src={img.url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── Details ──────────────────────── */}
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

          {/* Condition badge for sale listings */}
          {listing.type === 'SALE' && listing.sale_details?.condition && (
            <div className="flex items-center gap-2 mb-6">
              <span className="label mb-0">Condition:</span>
              <span className="badge-blue">{listing.sale_details.condition.replace('_', ' ')}</span>
              {listing.sale_details.is_negotiable && <span className="badge-yellow">Negotiable</span>}
            </div>
          )}

          {/* Rental date picker */}
          {listing.type === 'RENTAL' && !isOwner && (
            <div className="card p-4 mb-4 space-y-3">
              <p className="font-display font-semibold text-sm text-brand-ink">Select rental dates</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label text-xs">Start date</label>
                  <input type="date" className="input text-sm py-2"
                    value={startDate} onChange={(e) => setStartDate(e.target.value)}
                    min={format(new Date(), 'yyyy-MM-dd')} />
                </div>
                <div>
                  <label className="label text-xs">End date</label>
                  <input type="date" className="input text-sm py-2"
                    value={endDate} onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || format(new Date(), 'yyyy-MM-dd')} />
                </div>
              </div>
              {listing.rental_details?.deposit_amount > 0 && (
                <p className="text-xs text-brand-ink/40 font-mono">
                  + ${listing.rental_details.deposit_amount} deposit (refundable)
                </p>
              )}
            </div>
          )}

          {/* CTA */}
          {!isOwner && (
            <div className="space-y-3">
              {listing.type === 'SALE' && (
                <button onClick={() => isAuthenticated ? orderMutation.mutate() : navigate('/login')}
                  disabled={orderMutation.isPending}
                  className="btn-primary w-full justify-center text-base py-4">
                  {orderMutation.isPending ? 'Placing order...' : 'Buy now'}
                </button>
              )}
              {listing.type === 'RENTAL' && (
                <button
                  onClick={() => {
                    if (!isAuthenticated) return navigate('/login')
                    if (!startDate || !endDate) return toast.error('Select rental dates first')
                    rentalMutation.mutate()
                  }}
                  disabled={rentalMutation.isPending}
                  className="btn-primary w-full justify-center text-base py-4">
                  {rentalMutation.isPending ? 'Sending request...' : 'Request rental'}
                </button>
              )}
              {listing.type === 'SERVICE' && (
                <Link to={`/messages?listing=${id}`} className="btn-primary w-full justify-center text-base py-4">
                  Book this service
                </Link>
              )}
              <Link to={`/messages?listing=${id}`}
                className="btn-ghost w-full justify-center gap-2">
                <MessageSquare size={18} /> Message seller
              </Link>
            </div>
          )}

          {isOwner && (
            <div className="card-ink p-4 rounded-xl">
              <p className="font-display font-semibold text-white text-sm mb-1">This is your listing</p>
              <p className="text-white/50 text-xs font-body">Manage it from your dashboard</p>
              <Link to="/dashboard/my-listings" className="mt-3 inline-flex btn-primary btn-sm">
                Go to Dashboard
              </Link>
            </div>
          )}

          {/* Seller info */}
          <div className="mt-6 pt-6 border-t border-black/5">
            <p className="label">Listed by</p>
            <Link to={`/profile/${listing.user?.id}`} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 rounded-full bg-brand-ink overflow-hidden">
                {listing.user?.avatar_url
                  ? <img src={listing.user.avatar_url} alt="" className="w-full h-full object-cover" />
                  : <div className="w-full h-full flex items-center justify-center text-white font-display font-bold">
                      {listing.user?.first_name?.[0]}
                    </div>
                }
              </div>
              <div>
                <p className="font-display font-semibold text-sm">{listing.user?.first_name} {listing.user?.last_name}</p>
                <p className="text-xs text-brand-ink/50 font-mono">{listing.university}</p>
              </div>
            </Link>
          </div>

          {/* Trust badge */}
          <div className="flex items-center gap-2 mt-4 text-xs text-brand-ink/40 font-mono">
            <Shield size={12} className="text-brand-green" />
            Verified .edu student · Safe on-campus meetups
          </div>
        </div>
      </div>
    </div>
  )
}