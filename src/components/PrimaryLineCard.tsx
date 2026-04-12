import {
  ArrowRightIcon,
  ChartBarIcon,
  DevicePhoneMobileIcon,
  UsersIcon,
} from '@heroicons/react/24/outline'
import type { Line } from '../data'
import { ProgressBar } from './ProgressBar'

type PrimaryLineCardProps = {
  line: Line
  selected: boolean
  onSelect: (lineId: number) => void
  index: number
}

export function PrimaryLineCard({ line, selected, onSelect, index }: PrimaryLineCardProps) {
  const usedData = line.usedData

  return (
    <article
      className={`animate-card-in rounded-[2rem] border p-0 shadow-lg shadow-purple-200/40 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${
        selected
          ? 'border-[#9C27B0] bg-gradient-to-br from-[#6A1B9A] via-[#7B1FA2] to-[#9C27B0] text-white'
          : 'border-white/70 bg-white/95 text-slate-900'
      }`}
      style={{ animationDelay: `${index * 90}ms` }}
    >
      <div className={`rounded-[2rem] p-5 ${selected ? 'bg-white/10' : 'bg-transparent'}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div
              className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-[0.22em] ring-1 ring-inset ${selected ? 'bg-white/15 text-white ring-white/15' : 'bg-violet-50 text-violet-700 ring-violet-100'}`}
            >
              <DevicePhoneMobileIcon className="h-4 w-4" />
              Primary Line
            </div>
            <h3 className="mt-4 text-2xl font-black tracking-tight">{line.phone}</h3>
            <p className={`mt-1 text-sm font-medium ${selected ? 'text-white/75' : 'text-slate-500'}`}>
              {line.plan}
            </p>
          </div>
          <div className={`rounded-2xl px-4 py-3 text-right ring-1 ${selected ? 'bg-white/10 ring-white/10' : 'bg-violet-50 ring-violet-100'}`}>
            <p className={`text-xs font-semibold uppercase tracking-[0.18em] ${selected ? 'text-white/65' : 'text-violet-500'}`}>
              Renewal Day
            </p>
            <p className="mt-1 text-lg font-black">{line.renewalDay}</p>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className={`rounded-3xl px-4 py-4 ring-1 ${selected ? 'bg-white/10 ring-white/10' : 'bg-slate-50 ring-slate-200'}`}>
            <div className="flex items-center gap-2 text-sm font-semibold opacity-80">
              <ChartBarIcon className="h-4 w-4" />
              Total Package
            </div>
            <div className="mt-3 space-y-2 text-lg font-black">
              <div>📶 {line.totalData}GB</div>
              <div>📞 {line.totalMinutes} min</div>
            </div>
          </div>

          <div className={`rounded-3xl px-4 py-4 ring-1 ${selected ? 'bg-white/10 ring-white/10' : 'bg-slate-50 ring-slate-200'}`}>
            <div className="flex items-center gap-2 text-sm font-semibold opacity-80">
              <UsersIcon className="h-4 w-4" />
              Members
            </div>
            <p className="mt-3 text-3xl font-black">{line.membersCount}</p>
            <p className={`mt-1 text-sm ${selected ? 'text-white/75' : 'text-slate-500'}`}>
              shared allocations
            </p>
          </div>
        </div>

        <div className="mt-5">
          <ProgressBar
            label="Package usage"
            used={usedData}
            total={line.totalData}
            unit="GB"
            accent={selected ? 'emerald' : 'purple'}
          />
          <p className={`mt-3 text-sm font-semibold ${selected ? 'text-white/80' : 'text-slate-600'}`}>
            Used: {usedData}GB | Remaining: {line.totalData - usedData}GB
          </p>
        </div>

        <button
          type="button"
          onClick={() => onSelect(line.id)}
          className={`mt-5 inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-bold transition-all duration-300 ${
            selected
              ? 'bg-white text-[#6A1B9A] shadow-lg shadow-black/10'
              : 'bg-[#6A1B9A] text-white shadow-lg shadow-purple-300/60 hover:bg-[#7B1FA2]'
          }`}
        >
          View Details
          <ArrowRightIcon className="h-4 w-4" />
        </button>
      </div>
    </article>
  )
}