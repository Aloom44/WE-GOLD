type ProgressBarProps = {
  label: string
  used: number
  total: number
  unit: string
  accent: 'purple' | 'emerald'
}

const accentClasses = {
  purple: 'from-[#6A1B9A] via-[#8E24AA] to-[#9C27B0]',
  emerald: 'from-emerald-500 via-emerald-500 to-teal-500',
} as const

export function ProgressBar({ label, used, total, unit, accent }: ProgressBarProps) {
  const percentage = Math.min(100, Math.round((used / total) * 100))
  const remaining = Math.max(total - used, 0)
  const usedLabel = `${used}${unit ? ` ${unit}` : ''}`
  const remainingLabel = `${remaining}${unit ? ` ${unit}` : ''}`

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-200/60">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-500">{label}</p>
          <p className="mt-1 text-base font-bold text-slate-900">
            {usedLabel} used
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {percentage}%
        </span>
      </div>

      <div className="h-3 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${accentClasses[accent]} transition-[width] duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="mt-3 flex items-center justify-between text-sm font-medium text-slate-600">
        <span>Used: {usedLabel}</span>
        <span className="text-emerald-600">Remaining: {remainingLabel}</span>
      </div>
    </div>
  )
}