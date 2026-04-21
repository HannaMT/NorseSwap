import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, EyeOff, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react'
import { authApi } from '../api/client'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm()
  const email = watch('email', '')
  const isEdu = email.endsWith('.edu')

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      await authApi.register({
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
      })
      setDone(true)
    } catch {
      // toast handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center animate-slide-up">
          <div className="w-20 h-20 bg-brand-green/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={40} className="text-brand-green" />
          </div>
          <h1 className="font-display font-bold text-3xl text-brand-ink mb-3">Check your inbox!</h1>
          <p className="text-brand-ink/60 font-body leading-relaxed mb-8">
            We sent a verification link to <strong className="text-brand-ink">{email}</strong>.
            Click it to activate your account.
          </p>
          <Link to="/login" className="btn-primary">Go to login <ArrowRight size={18} /></Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen grid md:grid-cols-2">

      {/* Left — decorative */}
      <div className="hidden md:flex flex-col justify-between bg-brand-yellow p-12 relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-80 h-80 bg-brand-orange/20 rounded-full blur-2xl" />

        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-orange rounded-lg flex items-center justify-center">
            <span className="text-white font-display font-bold text-sm">NS</span>
          </div>
          <span className="font-display font-bold text-xl text-brand-ink">NorseSwap</span>
        </Link>

        <div>
          <h2 className="font-display font-bold text-4xl text-brand-ink leading-tight mb-4">
            Your campus.<br />Your economy.
          </h2>
          <p className="text-brand-ink/60 font-body text-lg">
            Join thousands of students already renting, selling, and connecting.
          </p>

          <div className="mt-8 grid grid-cols-2 gap-3">
            {[
              { emoji: '🆓', text: 'Free to join' },
              { emoji: '🔒', text: 'Verified students only' },
              { emoji: '💸', text: 'Earn from your stuff' },
              { emoji: '🎓', text: '50+ universities' },
            ].map(({ emoji, text }) => (
              <div key={text} className="flex items-center gap-2 bg-white/50 rounded-xl px-3 py-2">
                <span>{emoji}</span>
                <span className="text-sm font-body font-medium text-brand-ink">{text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-brand-ink/30 font-mono text-xs">Only .edu emails accepted</p>
      </div>

      {/* Right — form */}
      <div className="flex flex-col justify-center px-6 sm:px-12 py-12">
        <div className="max-w-sm w-full mx-auto">

          <Link to="/" className="flex items-center gap-2 mb-8 md:hidden">
            <div className="w-7 h-7 bg-brand-orange rounded-lg flex items-center justify-center">
              <span className="text-white font-display font-bold text-xs">NS</span>
            </div>
            <span className="font-display font-bold text-lg text-brand-ink">NorseSwap</span>
          </Link>

          <h1 className="font-display font-bold text-3xl text-brand-ink mb-1">Create account</h1>
          <p className="text-brand-ink/50 font-body mb-8">Start with your .edu email</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">First name</label>
                <input className={`input ${errors.first_name ? 'border-red-400' : ''}`}
                  placeholder="Alice"
                  {...register('first_name', { required: 'Required' })} />
                {errors.first_name && <p className="text-red-500 text-xs mt-1">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="label">Last name</label>
                <input className={`input ${errors.last_name ? 'border-red-400' : ''}`}
                  placeholder="Chen"
                  {...register('last_name', { required: 'Required' })} />
                {errors.last_name && <p className="text-red-500 text-xs mt-1">{errors.last_name.message}</p>}
              </div>
            </div>

            <div>
              <label className="label">University email</label>
              <div className="relative">
                <input type="email"
                  className={`input pr-10 ${errors.email ? 'border-red-400' : isEdu ? 'border-brand-green' : ''}`}
                  placeholder="you@university.edu"
                  {...register('email', {
                    required: 'Email is required',
                    validate: (v) => v.endsWith('.edu') || 'Must be a .edu email address',
                  })} />
                {isEdu && (
                  <CheckCircle2 size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-green" />
                )}
              </div>
              {errors.email
                ? <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
                : <p className="text-brand-ink/40 text-xs mt-1 font-mono">Must end in .edu</p>
              }
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'}
                  className={`input pr-12 ${errors.password ? 'border-red-400' : ''}`}
                  placeholder="Min 8 characters"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: { value: 8, message: 'At least 8 characters' },
                  })} />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-ink/30 hover:text-brand-ink/60">
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={loading}
              className="btn-primary w-full justify-center text-base py-3.5 disabled:opacity-50 mt-2">
              {loading
                ? <Loader2 size={18} className="animate-spin" />
                : <>Create account <ArrowRight size={18} /></>}
            </button>
          </form>

          <p className="text-center text-xs text-brand-ink/30 font-body mt-4 leading-relaxed">
            By signing up you agree to our Terms of Service and Privacy Policy.
          </p>

          <p className="text-center text-sm text-brand-ink/50 font-body mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-orange font-semibold hover:underline">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}