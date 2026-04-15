import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Upload, X, Image, Loader2, ArrowRight, Plus, GripVertical } from 'lucide-react'
import { listingsApi } from '../api/client'
import clsx from 'clsx'

const TYPES = [
  { value: 'RENTAL',  emoji: '📦', label: 'Rental',      desc: 'Lend something out by the day/week' },
  { value: 'SALE',    emoji: '🏷️', label: 'For Sale',    desc: 'Sell something you no longer need' },
  { value: 'SERVICE', emoji: '🎓', label: 'Service',     desc: 'Offer tutoring, rides, skills' },
]

const CATEGORIES = {
  RENTAL:  ['Bikes', 'Electronics', 'Furniture', 'Cameras', 'Sports Gear', 'Textbooks', 'Clothing', 'Tools', 'Other'],
  SALE:    ['Textbooks', 'Electronics', 'Furniture', 'Clothing', 'Gaming Gear', 'Kitchen', 'Sports', 'Art Supplies', 'Other'],
  SERVICE: ['Tutoring', 'Rides', 'Photography', 'Design', 'Coding', 'Writing', 'Fitness', 'Music', 'Other'],
}

const PERIODS = ['HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY']
const CONDITIONS = ['NEW', 'LIKE_NEW', 'GOOD', 'FAIR', 'POOR']

export default function CreateListing() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)        // 1=type, 2=details, 3=photos
  const [type, setType] = useState('')
  const [photos, setPhotos] = useState([])   // { file, preview }
  const [submitting, setSubmitting] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm()

  // ── Photo upload ─────────────────────────
  const onDrop = useCallback((acceptedFiles) => {
    const newPhotos = acceptedFiles
      .slice(0, 8 - photos.length)
      .map((file) => ({ file, preview: URL.createObjectURL(file) }))
    setPhotos((prev) => [...prev, ...newPhotos])
  }, [photos])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxFiles: 8,
    disabled: photos.length >= 8,
  })

  const removePhoto = (i) => {
    URL.revokeObjectURL(photos[i].preview)
    setPhotos((prev) => prev.filter((_, idx) => idx !== i))
  }

  // ── Submit ───────────────────────────────
  const onSubmit = async (data) => {
    if (!type) return toast.error('Please select a listing type')
    setSubmitting(true)

    try {
      const formData = new FormData()

      // Core fields
      formData.append('type', type)
      formData.append('title', data.title)
      formData.append('description', data.description)
      formData.append('category', data.category)
      formData.append('location', data.location || '')
      formData.append('allow_other_campuses', data.allow_other_campuses || false)
      if (data.tags) formData.append('tags', data.tags)

      // Type-specific fields
      if (type === 'RENTAL') {
        formData.append('rental_price_per_period', data.rental_price)
        formData.append('rental_price_period', data.rental_period)
        formData.append('rental_deposit', data.deposit || 0)
        formData.append('rental_min_days', data.min_days || 1)
      } else if (type === 'SALE') {
        formData.append('sale_price', data.sale_price)
        formData.append('sale_condition', data.condition)
        formData.append('sale_is_negotiable', data.negotiable || false)
        formData.append('sale_quantity', data.quantity || 1)
      } else if (type === 'SERVICE') {
        formData.append('service_category', data.service_category)
        formData.append('service_price_per_hour', data.hourly_rate)
        formData.append('service_skill_level', data.skill_level || '')
      }

      // Photos
      photos.forEach(({ file }) => formData.append('images', file))

      const res = await listingsApi.create(formData)
      toast.success('Listing posted!')
      navigate(`/listings/${res.data.id}`)
    } catch {
      // handled by interceptor
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-container py-10 max-w-3xl">
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-brand-ink">Post a listing</h1>
        <p className="text-brand-ink/50 font-body mt-1">Share something with your campus community</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-3 mb-8">
        {['Type', 'Details', 'Photos'].map((label, i) => (
          <div key={label} className="flex items-center gap-3">
            <div className={clsx(
              'w-8 h-8 rounded-full flex items-center justify-center font-display font-bold text-sm transition-all',
              step > i + 1 ? 'bg-brand-green text-white' :
              step === i + 1 ? 'bg-brand-orange text-white' :
              'bg-black/5 text-brand-ink/30'
            )}>
              {step > i + 1 ? '✓' : i + 1}
            </div>
            <span className={clsx('text-sm font-display font-semibold',
              step === i + 1 ? 'text-brand-ink' : 'text-brand-ink/30')}>
              {label}
            </span>
            {i < 2 && <div className="w-8 h-px bg-black/10" />}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>

        {/* ── Step 1: Type ─────────────────── */}
        {step === 1 && (
          <div className="animate-slide-up">
            <h2 className="font-display font-bold text-xl text-brand-ink mb-6">What are you listing?</h2>
            <div className="grid sm:grid-cols-3 gap-4 mb-8">
              {TYPES.map(({ value, emoji, label, desc }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setType(value)}
                  className={clsx(
                    'card p-6 text-left transition-all hover:-translate-y-0.5',
                    type === value
                      ? 'border-2 border-brand-orange ring-4 ring-brand-orange/10'
                      : 'border-2 border-transparent hover:border-black/10'
                  )}
                >
                  <span className="text-3xl block mb-3">{emoji}</span>
                  <h3 className="font-display font-bold text-brand-ink mb-1">{label}</h3>
                  <p className="text-xs text-brand-ink/50 font-body">{desc}</p>
                </button>
              ))}
            </div>
            <button type="button" disabled={!type} onClick={() => setStep(2)}
              className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed">
              Continue <ArrowRight size={18} />
            </button>
          </div>
        )}

        {/* ── Step 2: Details ──────────────── */}
        {step === 2 && (
          <div className="animate-slide-up space-y-5">
            <h2 className="font-display font-bold text-xl text-brand-ink">Listing details</h2>

            {/* Title */}
            <div>
              <label className="label">Title</label>
              <input className={`input ${errors.title ? 'border-red-400' : ''}`}
                placeholder={type === 'RENTAL' ? 'e.g. Trek Mountain Bike — Great condition' :
                             type === 'SERVICE' ? 'e.g. Calculus Tutoring — PhD Student' :
                             'e.g. CLRS Algorithms Textbook (4th ed.)'}
                {...register('title', { required: 'Title is required' })} />
              {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>}
            </div>

            {/* Description */}
            <div>
              <label className="label">Description</label>
              <textarea rows={4} className={`input resize-none ${errors.description ? 'border-red-400' : ''}`}
                placeholder="Describe your item or service in detail..."
                {...register('description', { required: 'Description is required' })} />
              {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description.message}</p>}
            </div>

            {/* Category */}
            <div>
              <label className="label">Category</label>
              <select className="input" {...register('category', { required: 'Category is required' })}>
                <option value="">Select a category</option>
                {(CATEGORIES[type] || []).map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              {errors.category && <p className="text-red-500 text-xs mt-1">{errors.category.message}</p>}
            </div>

            {/* Type-specific pricing */}
            {type === 'RENTAL' && (
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Price</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-ink/40 font-display font-semibold">$</span>
                    <input type="number" min="0" step="0.01" className="input pl-8"
                      placeholder="15.00"
                      {...register('rental_price', { required: true, min: 0 })} />
                  </div>
                </div>
                <div>
                  <label className="label">Per</label>
                  <select className="input" {...register('rental_period', { required: true })}>
                    {PERIODS.map((p) => <option key={p} value={p}>{p.charAt(0) + p.slice(1).toLowerCase()}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Deposit (optional)</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-ink/40 font-display font-semibold">$</span>
                    <input type="number" min="0" step="0.01" className="input pl-8" placeholder="0.00"
                      {...register('deposit')} />
                  </div>
                </div>
                <div>
                  <label className="label">Min. rental days</label>
                  <input type="number" min="1" className="input" placeholder="1"
                    {...register('min_days')} />
                </div>
              </div>
            )}

            {type === 'SALE' && (
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Price</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-ink/40 font-display font-semibold">$</span>
                    <input type="number" min="0" step="0.01" className="input pl-8" placeholder="45.00"
                      {...register('sale_price', { required: true })} />
                  </div>
                </div>
                <div>
                  <label className="label">Condition</label>
                  <select className="input" {...register('condition', { required: true })}>
                    {CONDITIONS.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
                  </select>
                </div>
                <div className="flex items-center gap-3">
                  <input type="checkbox" id="negotiable" className="w-4 h-4 accent-brand-orange"
                    {...register('negotiable')} />
                  <label htmlFor="negotiable" className="font-body text-sm text-brand-ink/70">Price is negotiable</label>
                </div>
                <div>
                  <label className="label">Quantity</label>
                  <input type="number" min="1" className="input" defaultValue={1}
                    {...register('quantity')} />
                </div>
              </div>
            )}

            {type === 'SERVICE' && (
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Hourly rate</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-ink/40 font-display font-semibold">$</span>
                    <input type="number" min="0" step="0.01" className="input pl-8" placeholder="30.00"
                      {...register('hourly_rate', { required: true })} />
                  </div>
                </div>
                <div>
                  <label className="label">Skill / experience level</label>
                  <input className="input" placeholder="e.g. PhD Student, 5 years exp."
                    {...register('skill_level')} />
                </div>
              </div>
            )}

            {/* Location */}
            <div>
              <label className="label">Location on campus (optional)</label>
              <input className="input" placeholder="e.g. East Campus, Building 32"
                {...register('location')} />
            </div>

            {/* Tags */}
            <div>
              <label className="label">Tags <span className="text-brand-ink/30 font-normal">(comma separated)</span></label>
              <input className="input" placeholder="algorithms, cs, textbook"
                {...register('tags')} />
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={() => setStep(1)} className="btn-ghost">Back</button>
              <button type="button" onClick={() => setStep(3)} className="btn-primary">
                Add photos <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Photos ───────────────── */}
        {step === 3 && (
          <div className="animate-slide-up">
            <h2 className="font-display font-bold text-xl text-brand-ink mb-2">Add photos</h2>
            <p className="text-brand-ink/50 font-body text-sm mb-6">
              Up to 8 photos. First photo will be the cover image.
            </p>

            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={clsx(
                'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200',
                isDragActive
                  ? 'border-brand-orange bg-brand-orange/5 scale-[1.01]'
                  : photos.length >= 8
                  ? 'border-black/10 bg-black/2 opacity-50 cursor-not-allowed'
                  : 'border-black/15 hover:border-brand-orange/50 hover:bg-brand-orange/3'
              )}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 bg-brand-orange/10 rounded-2xl flex items-center justify-center">
                  <Upload size={24} className="text-brand-orange" />
                </div>
                {isDragActive ? (
                  <p className="font-display font-semibold text-brand-orange">Drop to upload!</p>
                ) : (
                  <>
                    <p className="font-display font-semibold text-brand-ink">
                      Drag & drop photos here
                    </p>
                    <p className="text-sm text-brand-ink/40 font-body">
                      or <span className="text-brand-orange">browse files</span> · JPEG, PNG, WebP · max 10MB each
                    </p>
                  </>
                )}
                <p className="text-xs text-brand-ink/30 font-mono">
                  {photos.length}/8 photos added
                </p>
              </div>
            </div>

            {/* Photo previews */}
            {photos.length > 0 && (
              <div className="grid grid-cols-4 gap-3 mt-4">
                {photos.map((photo, i) => (
                  <div key={i} className="relative aspect-square rounded-xl overflow-hidden group">
                    <img src={photo.preview} alt="" className="w-full h-full object-cover" />
                    {i === 0 && (
                      <div className="absolute bottom-0 left-0 right-0 bg-brand-orange/90 text-white text-xs font-mono py-1 text-center">
                        Cover
                      </div>
                    )}
                    <button type="button" onClick={() => removePhoto(i)}
                      className="absolute top-1.5 right-1.5 w-6 h-6 bg-black/60 text-white rounded-full
                                 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity
                                 hover:bg-red-500">
                      <X size={12} />
                    </button>
                  </div>
                ))}
                {photos.length < 8 && (
                  <div {...getRootProps()}
                    className="aspect-square rounded-xl border-2 border-dashed border-black/10
                               flex items-center justify-center cursor-pointer hover:border-brand-orange/50 transition-colors">
                    <input {...getInputProps()} />
                    <Plus size={20} className="text-brand-ink/30" />
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-3 mt-8">
              <button type="button" onClick={() => setStep(2)} className="btn-ghost">Back</button>
              <button type="submit" disabled={submitting}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
                {submitting
                  ? <><Loader2 size={18} className="animate-spin" /> Posting...</>
                  : <>Post listing <ArrowRight size={18} /></>
                }
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}