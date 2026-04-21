import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, SlidersHorizontal, X, Heart, MapPin, Star } from 'lucide-react'
import { listingsApi } from '../api/client'
import clsx from 'clsx'

const TYPES   = [{ value: '', label: 'All' }, { value: 'RENTAL', label: 'Rentals' }, { value: 'SALE', label: 'For Sale' }, { value: 'SERVICE', label: 'Services' }]
const SORTS   = [{ value: 'newest', label: 'Newest' }, { value: 'popular', label: 'Popular' }]
const CATEGORIES = ['Textbooks', 'Bikes', 'Furniture', 'Electronics', 'Clothing', 'Tutoring', 'Photography', 'Rides', 'Gaming Gear', 'Other']

function ListingCard({ listing }) {
  const rawPrimaryImage = listing.images?.find((i) => i.is_primary)?.url
const primaryImage = rawPrimaryImage?.startsWith('/static/')
  ? `http://localhost:8000${rawPrimaryImage}`
  : rawPrimaryImage


  const price =
    listing.rental_details?.price_per_period ??
    listing.sale_details?.price ??
    listing.service_details?.price_per_hour

  const priceLabel =
    listing.type === 'RENTAL'  ? `$${price}/${listing.rental_details?.price_period?.toLowerCase() ?? 'day'}` :
    listing.type === 'SERVICE' ? `$${price}/hr` :
    `$${price}`

  const typeColors = {
    RENTAL:  'type-chip-rental',
    SALE:    'type-chip-sale',
    SERVICE: 'type-chip-service',
  }

  return (
    <Link to={`/listings/${listing.id}`}
      className="card group overflow-hidden flex flex-col animate-fade-in">
      {/* Image */}
      <div className="relative aspect-[4/3] bg-brand-ink/5 overflow-hidden">
        {primaryImage ? (
          <img src={primaryImage} alt={listing.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">
            {listing.type === 'RENTAL' ? '📦' : listing.type === 'SERVICE' ? '🎓' : '🏷️'}
          </div>
        )}
        <div className="absolute top-3 left-3">
          <span className={typeColors[listing.type]}>{listing.type.toLowerCase()}</span>
        </div>
        <button className="absolute top-3 right-3 w-8 h-8 bg-white rounded-full flex items-center justify-center
                           shadow-sm opacity-0 group-hover:opacity-100 transition-opacity hover:scale-110 active:scale-95">
          <Heart size={14} className={listing.is_saved ? 'fill-brand-orange text-brand-orange' : 'text-brand-ink/50'} />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-display font-semibold text-sm text-brand-ink line-clamp-2 flex-1">
            {listing.title}
          </h3>
          <span className="font-display font-bold text-brand-orange whitespace-nowrap text-sm">
            {priceLabel}
          </span>
        </div>

        <p className="text-xs text-brand-ink/50 font-body line-clamp-2 mb-3 flex-1">
          {listing.description}
        </p>

        <div className="flex items-center justify-between pt-3 border-t border-black/5">
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded-full bg-brand-ink overflow-hidden">
              {listing.user?.avatar_url
                ? <img src={listing.user.avatar_url} alt="" className="w-full h-full object-cover" />
                : <span className="text-white text-xs flex items-center justify-center h-full font-display">
                    {listing.user?.first_name?.[0]}
                  </span>
              }
            </div>
            <span className="text-xs text-brand-ink/50 font-body">{listing.user?.first_name}</span>
          </div>
          {listing.location && (
            <div className="flex items-center gap-0.5 text-xs text-brand-ink/30 font-mono">
              <MapPin size={10} />
              <span className="truncate max-w-20">{listing.location}</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

export default function BrowsePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showFilters, setShowFilters] = useState(false)

  const [filters, setFilters] = useState({
    type: searchParams.get('type') || '',
    category: searchParams.get('category') || '',
    search: searchParams.get('search') || '',
    sort_by: 'newest',
    page: 1,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['listings', filters],
    queryFn: () => listingsApi.getAll(filters).then((r) => r.data),
  })

  const setFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }))
    setSearchParams((prev) => {
      if (value) prev.set(key, value)
      else prev.delete(key)
      return prev
    })
  }

  return (
    <div className="page-container py-10">

      {/* ── Header ───────────────────────────── */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display font-bold text-3xl text-brand-ink">Browse listings</h1>
          {data && (
            <p className="text-brand-ink/50 text-sm font-body mt-0.5">
              {data.total.toLocaleString()} listings found
            </p>
          )}
        </div>
        <button onClick={() => setShowFilters(!showFilters)}
          className={clsx('flex items-center gap-2 px-4 py-2 rounded-xl border-2 font-display font-semibold text-sm transition-colors',
            showFilters ? 'border-brand-orange bg-brand-orange/5 text-brand-orange' : 'border-black/10 hover:border-brand-orange/50')}>
          <SlidersHorizontal size={16} />
          Filters
        </button>
      </div>

      {/* ── Search bar ───────────────────────── */}
      <div className="relative mb-6">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-ink/30" />
        <input
          className="input pl-11 text-base"
          placeholder="Search listings, textbooks, bikes..."
          value={filters.search}
          onChange={(e) => setFilter('search', e.target.value)}
        />
        {filters.search && (
          <button onClick={() => setFilter('search', '')}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-brand-ink/30 hover:text-brand-ink/60">
            <X size={16} />
          </button>
        )}
      </div>

      {/* ── Type tabs ────────────────────────── */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {TYPES.map(({ value, label }) => (
          <button key={value}
            onClick={() => setFilter('type', value)}
            className={clsx(
              'px-5 py-2 rounded-full font-display font-semibold text-sm whitespace-nowrap transition-all',
              filters.type === value
                ? 'bg-brand-ink text-white shadow-md'
                : 'bg-white border border-black/10 text-brand-ink/60 hover:border-brand-ink/30'
            )}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Expanded filters ─────────────────── */}
      {showFilters && (
        <div className="card p-5 mb-6 animate-slide-up">
          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <label className="label">Category</label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((cat) => (
                  <button key={cat}
                    onClick={() => setFilter('category', filters.category === cat ? '' : cat)}
                    className={clsx(
                      'px-3 py-1 rounded-lg text-xs font-display font-semibold border transition-all',
                      filters.category === cat
                        ? 'bg-brand-orange text-white border-brand-orange'
                        : 'border-black/10 text-brand-ink/60 hover:border-brand-orange/50'
                    )}>
                    {cat}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Sort by</label>
              <div className="flex gap-2">
                {SORTS.map(({ value, label }) => (
                  <button key={value}
                    onClick={() => setFilter('sort_by', value)}
                    className={clsx(
                      'px-4 py-2 rounded-lg text-sm font-display font-semibold border transition-all',
                      filters.sort_by === value
                        ? 'bg-brand-ink text-white border-brand-ink'
                        : 'border-black/10 text-brand-ink/60 hover:border-brand-ink/30'
                    )}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Results grid ─────────────────────── */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="card overflow-hidden animate-pulse">
              <div className="aspect-[4/3] bg-black/5" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-black/5 rounded w-3/4" />
                <div className="h-3 bg-black/5 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : data?.listings?.length === 0 ? (
        <div className="text-center py-24">
          <p className="text-5xl mb-4">🔍</p>
          <h3 className="font-display font-bold text-xl text-brand-ink mb-2">No listings found</h3>
          <p className="text-brand-ink/50 font-body">Try adjusting your filters or search terms</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {data?.listings?.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>

          {/* Pagination */}
          {data?.pages > 1 && (
            <div className="flex justify-center gap-2 mt-10">
              {Array.from({ length: data.pages }, (_, i) => i + 1).map((p) => (
                <button key={p}
                  onClick={() => setFilters((prev) => ({ ...prev, page: p }))}
                  className={clsx(
                    'w-9 h-9 rounded-lg font-display font-semibold text-sm transition-all',
                    filters.page === p ? 'bg-brand-ink text-white' : 'bg-white border border-black/10 hover:border-brand-ink/30'
                  )}>
                  {p}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}