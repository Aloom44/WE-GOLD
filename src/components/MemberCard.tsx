import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline'
import { StatusBadge, type MemberStatus } from './StatusBadge'

export type Member = {
  id: number
  name: string
  phone: string
  dataAllocation: number
  minuteAllocation: number
  amountDue: number
  amountPaid: number
  status: MemberStatus
}

type MemberCardProps = {
  member: Member
  onEdit: (member: Member) => void
  onDelete: (memberId: number) => void
}

export function MemberCard({ member, onEdit, onDelete }: MemberCardProps) {
  return (
    <article className="group rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/70 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-purple-200/40">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">{member.name}</h3>
          <p className="mt-1 text-sm font-medium text-slate-500">{member.phone}</p>
        </div>
        <StatusBadge status={member.status} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-2xl bg-violet-50 px-3 py-3 text-violet-700 ring-1 ring-violet-100">
          <p className="text-xs font-semibold uppercase tracking-wide text-violet-500">Data</p>
          <p className="mt-1 text-base font-bold">{member.dataAllocation}GB</p>
        </div>
        <div className="rounded-2xl bg-sky-50 px-3 py-3 text-sky-700 ring-1 ring-sky-100">
          <p className="text-xs font-semibold uppercase tracking-wide text-sky-500">Minutes</p>
          <p className="mt-1 text-base font-bold">{member.minuteAllocation} min</p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 ring-1 ring-slate-200">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Payment</p>
        <p className="mt-1 text-base font-bold text-slate-900">
          {member.amountPaid} / {member.amountDue} EGP
        </p>
      </div>

      <div className="mt-5 flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={() => onEdit(member)}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-violet-200 hover:text-violet-700"
        >
          <PencilSquareIcon className="h-4 w-4" />
          Edit
        </button>
        <button
          type="button"
          onClick={() => onDelete(member.id)}
          className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:-translate-y-0.5 hover:bg-rose-100"
        >
          <TrashIcon className="h-4 w-4" />
          Delete
        </button>
      </div>
    </article>
  )
}