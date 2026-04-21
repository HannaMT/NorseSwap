import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react'
import { authApi } from '../api/client'
import useAuthStore from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((s) => s.login)
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)

  const from = location.state?.from?.pathname || '/browse'

  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const res = await authApi.login(data)
      login(res.data, res.data.user)
      toast.success(`Welcome back, ${res.data.user.first_name}!`)
      navigate(from, { replace: true })
    } catch (err) {
      // Error toast handled by axios interceptor
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen grid md:grid-cols-2">

      {/* Left — decorative */}
      <div className="hidden md:flex flex-col justify-between bg-brand-ink p-12 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full opacity-[0.03]"
          style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 bg-brand-orange/20 rounded-full blur-3xl" />

        <Link to="/" className="flex items-center gap-2 z-10">
          <div className="w-8 h-8 bg-brand-orange rounded-lg flex items-center justify-center">
            <span className="text-white font-display font-bold text-sm">NS</span>
          </div>
          <span className="font-display font-bold text-xl text-white">NorseSwap</span>
        </Link>

        <div className="z-10">
          <blockquote className="font-display text-3xl font-bold text-white leading-tight mb-6">
            "Made back my textbook money in the first week."
          </blockquote>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-orange rounded-full flex items-center justify-center font-display font-bold text-white">
              A
            </div>
            <div>
              <p className="font-display font-semibold text-white text-sm">Alice Chen</p>
              <p className="text-white/40 text-xs font-mono">MIT · Class of 2026</p>
            </div>
          </div>
        </div>

        <div className="flex gap-3 z-10">
          {['📚 Textbooks', '🚲 Bikes', '🎓 Tutoring'].map((t) => (
            <span key={t} className="px-3 py-1.5 bg-white/10 rounded-full text-white/60 text-xs font-mono">{t}</span>
          ))}
        </div>
      </div>

      {/* Right — form */}
      <div className="flex flex-col justify-center px-6 sm:px-12 py-12">
        <div className="max-w-sm w-full mx-auto">

          {/* Mobile logo */}
          <Link to="/" className="flex items-center gap-2 mb-8 md:hidden">
            <div className="w-7 h-7 bg-brand-orange rounded-lg flex items-center justify-center">
              <span className="text-white font-display font-bold text-xs">NS</span>
            </div>
            <span className="font-display font-bold text-lg text-brand-ink">NorseSwap</span>
          </Link>

          <h1 className="font-display font-bold text-3xl text-brand-ink mb-1">Welcome back</h1>
          <p className="text-brand-ink/50 font-body mb-8">Log in to your student account</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="label">University email</label>
              <input
                type="email"
                placeholder="you@university.edu"
                className={`input ${errors.email ? 'border-red-400' : ''}`}
                {...register('email', { required: 'Email is required' })}
              />
              {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="label mb-0">Password</label>
                <Link to="/forgot-password" className="text-xs text-brand-orange hover:underline font-body">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  placeholder="••••••••"
                  className={`input pr-12 ${errors.password ? 'border-red-400' : ''}`}
                  {...register('password', { required: 'Password is required' })}
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-ink/30 hover:text-brand-ink/60">
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={loading}
              className="btn-primary w-full justify-center text-base py-3.5 disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <>Log in <ArrowRight size={18} /></>}
            </button>
          </form>

          <p className="text-center text-sm text-brand-ink/50 font-body mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-brand-orange font-semibold hover:underline">
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}