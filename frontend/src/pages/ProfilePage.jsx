import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MapPin, Star, Package, Calendar } from 'lucide-react'
import { usersApi, reviewsApi } from '../api/client'
import { format } from 'date-fns'

export default function ProfilePage() {
  const { id } = useParams()

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile', id],
    queryFn: () => usersApi.getProfile(id).then((r) => r.data),
  })

  const { data: reviews } = useQuery({
    queryKey: ['reviews', id],
    queryFn: () => reviewsApi.getUserReviews(id).then((r) => r.data),
  })

  const { data: listings } = useQuery({
    queryKey: ['user-listings', id],
    queryFn: () => usersApi.getProfile(id).then(() => []), // placeholder
  })

  if (isLoading) return (
    <div className="page-container py-10 animate-pulse">
      <div className="flex items-center gap-6 mb-8">
        <div className="w-20 h-20 rounded-full bg-black/5" />
        <div className="space-y-2">
          <div className="h-6 bg-black/5 rounded w-40" />
          <div className="h-4 bg-black/5 rounded w-24" />
        </div>
      </div>
    </div>
  )

  if (!profile) return (
    <div className="page-container py-20 text-center">
      <h2 className="font-display font-bold text-2xl">User not found</h2>
    </div>
  )

  return (
    <div className="page-container py-10 max-w-3xl">
      {/* Profile header */}
      <div className="card p-6 flex items-start gap-5 mb-6">
        <div className="w-20 h-20 rounded-2xl bg-brand-ink overflow-hidden flex-shrink-0">
          {profile.avatar_url
            ? <img src={profile.avatar_url} alt="" className="w-full h-full object-cover" />
            : <div className="w-full h-full flex items-center justify-center text-white font-display font-bold text-2xl">
                {profile.first_name?.[0]}
              </div>
          }
        </div>
        <div className="flex-1">
          <h1 className="font-display font-bold text-2xl text-brand-ink">
            {profile.first_name} {profile.last_name}
          </h1>
          <p className="text-brand-ink/50 font-mono text-sm">{profile.university}</p>
          {profile.bio && <p className="text-brand-ink/70 font-body text-sm mt-2 leading-relaxed">{profile.bio}</p>}
          <div className="flex gap-4 mt-3">
            <div className="text-center">
              <p className="font-display font-bold text-brand-ink">{reviews?.total_reviews || 0}</p>
              <p className="text-xs text-brand-ink/40 font-mono">reviews</p>
            </div>
            <div className="text-center">
              <p className="font-display font-bold text-brand-orange">{reviews?.average_rating || '—'}</p>
              <p className="text-xs text-brand-ink/40 font-mono">avg rating</p>
            </div>
            <div className="text-center">
              <p className="font-display font-bold text-brand-ink">{profile.active_listings_count}</p>
              <p className="text-xs text-brand-ink/40 font-mono">listings</p>
            </div>
          </div>
        </div>
      </div>

      {/* Reviews */}
      {reviews?.reviews?.length > 0 && (
        <div>
          <h2 className="font-display font-bold text-xl text-brand-ink mb-4">Reviews</h2>
          <div className="space-y-3">
            {reviews.reviews.map((review) => (
              <div key={review.id} className="card p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-brand-ink overflow-hidden">
                      {review.reviewer?.avatar_url
                        ? <img src={review.reviewer.avatar_url} alt="" className="w-full h-full object-cover" />
                        : <div className="w-full h-full flex items-center justify-center text-white text-xs font-display">
                            {review.reviewer?.first_name?.[0]}
                          </div>
                      }
                    </div>
                    <span className="font-display font-semibold text-sm">{review.reviewer?.first_name}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {'★'.repeat(review.rating).split('').map((s, i) => (
                      <span key={i} className="text-brand-yellow text-sm">★</span>
                    ))}
                  </div>
                </div>
                {review.comment && <p className="text-sm text-brand-ink/70 font-body">{review.comment}</p>}
                <p className="text-xs text-brand-ink/30 font-mono mt-2">
                  {format(new Date(review.created_at), 'MMM d, yyyy')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}