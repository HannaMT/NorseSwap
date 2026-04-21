import { Link } from 'react-router-dom'
import { ArrowRight, Bike, BookOpen, Zap, Star, Shield, Users, ChevronRight } from 'lucide-react'

const MARQUEE_ITEMS = [
  '🚲 Rent a bike',  '📚 Sell textbooks', '🎸 Teach guitar',
  '💻 Swap laptops', '🏋️ Personal training', '📸 Photo shoots',
  '🛋️ Dorm furniture', '🧑‍🏫 Tutoring', '🎮 Gaming gear',
  '🧥 Vintage clothes', '🔬 Lab equipment', '🚗 Rides',
]

// const STATS = [
//   { value: '12K+', label: 'Students' },
//   { value: '3.2K', label: 'Active listings' },
//   { value: '50+', label: 'Universities' },
//   { value: '4.9★', label: 'Avg. rating' },
// ]

const HOW_IT_WORKS = [
  {
    step: '01',
    icon: Shield,
    title: 'Verify your .edu',
    body: 'Sign up with your university email. Every person on NorseSwap is a real, verified student.',
    color: 'bg-blue-500',
  },
  {
    step: '02',
    icon: Zap,
    title: 'Browse or post',
    body: 'Find what you need from students nearby, or list something you own in under 2 minutes.',
    color: 'bg-brand-orange',
  },
  {
    step: '03',
    icon: Star,
    title: 'Transact safely',
    body: 'Meet on campus, pay securely, and leave a review. Build your student reputation.',
    color: 'bg-brand-green',
  },
]

const CATEGORIES = [
  { emoji: '📚', label: 'Textbooks',    type: 'SALE' },
  { emoji: '🚲', label: 'Bikes',        type: 'RENTAL' },
  { emoji: '🛋️', label: 'Furniture',   type: 'SALE' },
  { emoji: '🧑‍💻', label: 'Tutoring',  type: 'SERVICE' },
  { emoji: '📷', label: 'Photography',  type: 'SERVICE' },
  { emoji: '🎮', label: 'Gaming Gear',  type: 'SALE' },
  { emoji: '🚗', label: 'Rides',        type: 'SERVICE' },
  { emoji: '🧥', label: 'Clothing',     type: 'SALE' },
]

export default function LandingPage() {
  return (
    <div className="overflow-hidden">

      {/* ── Hero ─────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col justify-center bg-brand-ink overflow-hidden">

        {/* Background blobs */}
        <div className="absolute top-1/4 -left-32 w-96 h-96 bg-brand-orange/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-brand-green/15 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-blue/10 rounded-full blur-3xl" />

        {/* Grid overlay */}
        <div className="absolute inset-0 opacity-[0.04]"
          style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '60px 60px' }} />

        <div className="page-container relative z-10 pt-24 pb-16">
          <div className="max-w-4xl">

            {/* Tag */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm
                            border border-white/20 rounded-full text-white/80 text-sm font-mono mb-8
                            animate-fade-in">
              <span className="w-2 h-2 bg-brand-green rounded-full animate-pulse" />
              Only for verified .edu students
            </div>

            {/* Headline */}
            <h1 className="font-display font-bold text-white leading-[1.05] mb-6 animate-slide-up">
              <span className="block text-5xl sm:text-7xl lg:text-8xl">The marketplace</span>
              <span className="block text-5xl sm:text-7xl lg:text-8xl">
                built for{' '}
                <span className="relative inline-block">
                  <span className="text-brand-orange">campus life.</span>
                  <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 300 12" fill="none">
                    <path d="M2 10 C75 2, 225 2, 298 10" stroke="#FFD93D" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                </span>
              </span>
            </h1>

            <p className="text-xl text-white/60 font-body max-w-xl leading-relaxed mb-10 animate-slide-up stagger-2">
              Rent bikes, sell textbooks, offer tutoring, find rides —
              all with verified students from your university.
            </p>

            <div className="flex flex-wrap gap-4 animate-slide-up stagger-3">
              <Link to="/register" className="btn-primary text-base px-8 py-4 shadow-xl shadow-orange-500/30">
                Get started free <ArrowRight size={18} />
              </Link>
              <Link to="/browse" className="inline-flex items-center gap-2 px-8 py-4 bg-white/10
                backdrop-blur-sm border border-white/20 text-white font-display font-semibold
                rounded-xl hover:bg-white/15 transition-all duration-150 text-base">
                Browse listings
              </Link>
            </div>

            {/* Stats row */}
            {/* <div className="flex flex-wrap gap-8 mt-16 animate-slide-up stagger-4">
              {STATS.map(({ value, label }) => (
                <div key={label}>
                  <p className="font-display font-bold text-3xl text-white">{value}</p>
                  <p className="text-sm text-white/40 font-body">{label}</p>
                </div>
              ))}
            </div> */}
          </div>
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white/30 animate-bounce">
          <span className="text-xs font-mono">scroll</span>
          <div className="w-px h-8 bg-white/20" />
        </div>
      </section>

      {/* ── Marquee ticker ───────────────────── */}
      <div className="bg-brand-orange py-4 overflow-hidden">
        <div className="flex animate-marquee whitespace-nowrap">
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, i) => (
            <span key={i} className="mx-8 text-white font-display font-semibold text-sm">
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* ── Categories ───────────────────────── */}
      <section className="py-24 page-container">
        <div className="flex items-end justify-between mb-12">
          <div>
            <div className="section-tag">Browse by category</div>
            <h2 className="font-display font-bold text-4xl sm:text-5xl text-brand-ink">
              What are you<br />looking for?
            </h2>
          </div>
          <Link to="/browse" className="hidden sm:flex items-center gap-1 text-brand-orange font-display font-semibold hover:gap-2 transition-all">
            View all <ChevronRight size={18} />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {CATEGORIES.map(({ emoji, label, type }, i) => (
            <Link
              key={label}
              to={`/browse?category=${label}&type=${type}`}
              className={`card p-6 flex flex-col items-center justify-center gap-3 text-center
                         hover:-translate-y-1 active:scale-95 transition-all duration-200
                         animate-slide-up`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <span className="text-4xl">{emoji}</span>
              <span className="font-display font-semibold text-sm text-brand-ink">{label}</span>
              <span className={`text-xs font-mono px-2 py-0.5 rounded-full
                ${type === 'RENTAL'  ? 'bg-blue-100 text-blue-600' :
                  type === 'SERVICE' ? 'bg-emerald-100 text-emerald-600' :
                                       'bg-orange-100 text-orange-600'}`}>
                {type.toLowerCase()}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* ── How it works ─────────────────────── */}
      <section className="py-24 bg-brand-ink">
        <div className="page-container">
          <div className="text-center mb-16">
            <div className="section-tag mx-auto">Simple by design</div>
            <h2 className="font-display font-bold text-4xl sm:text-5xl text-white">
              Up and running in minutes
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map(({ step, icon: Icon, title, body, color }, i) => (
              <div key={step} className="relative animate-slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                {i < HOW_IT_WORKS.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-full w-full h-px bg-white/10 z-0" />
                )}
                <div className={`w-16 h-16 ${color} rounded-2xl flex items-center justify-center mb-6 relative z-10`}>
                  <Icon size={28} className="text-white" />
                </div>
                <p className="font-mono text-xs text-white/30 mb-2">{step}</p>
                <h3 className="font-display font-bold text-xl text-white mb-3">{title}</h3>
                <p className="text-white/50 font-body leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────── */}
      <section className="py-24 page-container">
        <div className="bg-brand-orange rounded-3xl p-12 sm:p-16 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-black/10 rounded-full translate-y-1/2 -translate-x-1/2" />
          <div className="relative z-10">
            <h2 className="font-display font-bold text-4xl sm:text-5xl text-white mb-4">
              Your campus economy<br />starts here.
            </h2>
            <p className="text-white/80 font-body text-lg max-w-md mx-auto mb-8">
              Join thousands of students already buying, renting, and connecting on NorseSwap.
            </p>
            <Link to="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-brand-ink text-white
                         font-display font-bold rounded-xl hover:bg-zinc-800 transition-colors
                         text-lg shadow-2xl">
              Create free account <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}