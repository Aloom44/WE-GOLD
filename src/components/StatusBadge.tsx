import {
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/solid'

export type MemberStatus = 'paid' | 'partial' | 'unpaid'

type StatusBadgeProps = {
  status: MemberStatus
}

const config = {
  paid: {
    label: 'Paid',
    className: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    icon: CheckCircleIcon,
  },
  partial: {
    label: 'Partial',
    className: 'bg-amber-50 text-amber-700 ring-amber-200',
    icon: ClockIcon,
  },
  unpaid: {
    label: 'Unpaid',
    className: 'bg-rose-50 text-rose-700 ring-rose-200',
    icon: ExclamationTriangleIcon,
  },
} satisfies Record<MemberStatus, { label: string; className: string; icon: typeof CheckCircleIcon }>

export function StatusBadge({ status }: StatusBadgeProps) {
  const badge = config[status]
  const Icon = badge.icon

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ring-1 ${badge.className}`}
    >
      <Icon className="h-4 w-4" />
      {badge.label}
    </span>
  )
}