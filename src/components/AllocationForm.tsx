import { useEffect, useMemo, useState } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import type { Line } from '../data'
import type { Member } from './MemberCard'

export type MemberDraft = {
  name: string
  phone: string
  dataAllocation: number
  minuteAllocation: number
  amountDue: number
  amountPaid: number
}

type AllocationFormProps = {
  line: Line
  isOpen: boolean
  member: Member | null
  onClose: () => void
  onSubmit: (draft: MemberDraft, memberId?: number) => void
}

const emptyDraft: MemberDraft = {
  name: '',
  phone: '',
  dataAllocation: 0,
  minuteAllocation: 0,
  amountDue: 0,
  amountPaid: 0,
}

export function AllocationForm({ line, isOpen, member, onClose, onSubmit }: AllocationFormProps) {
  const [draft, setDraft] = useState<MemberDraft>(emptyDraft)

  useEffect(() => {
    if (isOpen) {
      setDraft(
        member
          ? {
              name: member.name,
              phone: member.phone,
              dataAllocation: member.dataAllocation,
              minuteAllocation: member.minuteAllocation,
              amountDue: member.amountDue,
              amountPaid: member.amountPaid,
            }
          : {
              ...emptyDraft,
              dataAllocation: 10,
              minuteAllocation: 1000,
              amountDue: 50,
              amountPaid: 0,
            },
      )
    }
  }, [isOpen, member, line.id])

  const remaining = useMemo(
    () => ({
      data: Math.max(line.totalData - Number(draft.dataAllocation || 0), 0),
      minutes: Math.max(line.totalMinutes - Number(draft.minuteAllocation || 0), 0),
    }),
    [draft.dataAllocation, draft.minuteAllocation, line.totalData, line.totalMinutes],
  )

  if (!isOpen) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/55 px-4 py-4 backdrop-blur-sm sm:items-center">
      <div className="w-full max-w-2xl animate-card-in rounded-[2rem] border border-white/70 bg-white shadow-2xl shadow-slate-950/20">
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-violet-500">
              Add Member
            </p>
            <h2 className="mt-2 text-2xl font-black text-slate-900">
              {member ? 'Edit Member' : 'New Allocation'}
            </h2>
            <p className="mt-1 text-sm font-medium text-slate-500">
              {line.phone} • {line.plan}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-200 bg-slate-50 p-2 text-slate-600 transition hover:bg-slate-100"
            aria-label="Close modal"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="px-5 py-5 sm:px-6">
          <div className="rounded-3xl border border-violet-100 bg-gradient-to-r from-violet-50 via-fuchsia-50 to-white p-4 text-slate-900">
            <p className="text-sm font-semibold text-violet-700">Remaining</p>
            <p className="mt-1 text-2xl font-black">
              {remaining.data}GB / {remaining.minutes} min
            </p>
            <p className="mt-2 text-sm font-medium text-slate-600">
              Updates live while you type. This is the remaining balance after the current form values.
            </p>
          </div>

          <form
            className="mt-5 grid gap-4 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault()
              onSubmit(draft, member?.id)
            }}
          >
            <Field
              label="Name"
              value={draft.name}
              onChange={(value) => setDraft((current) => ({ ...current, name: value }))}
              placeholder="Enter member name"
            />
            <Field
              label="Phone"
              value={draft.phone}
              onChange={(value) => setDraft((current) => ({ ...current, phone: value }))}
              placeholder="01xxxxxxxxx"
            />
            <Field
              label="Data allocation"
              type="number"
              value={String(draft.dataAllocation)}
              onChange={(value) => setDraft((current) => ({ ...current, dataAllocation: Number(value) }))}
              placeholder="10"
              suffix="GB"
            />
            <Field
              label="Minutes allocation"
              type="number"
              value={String(draft.minuteAllocation)}
              onChange={(value) => setDraft((current) => ({ ...current, minuteAllocation: Number(value) }))}
              placeholder="1000"
              suffix="min"
            />
            <Field
              label="Amount due"
              type="number"
              value={String(draft.amountDue)}
              onChange={(value) => setDraft((current) => ({ ...current, amountDue: Number(value) }))}
              placeholder="50"
              suffix="EGP"
            />
            <Field
              label="Amount paid"
              type="number"
              value={String(draft.amountPaid)}
              onChange={(value) => setDraft((current) => ({ ...current, amountPaid: Number(value) }))}
              placeholder="30"
              suffix="EGP"
            />

            <div className="sm:col-span-2 mt-2 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-slate-200 bg-white px-5 py-3 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-full bg-gradient-to-r from-[#6A1B9A] to-[#9C27B0] px-5 py-3 text-sm font-bold text-white shadow-lg shadow-purple-200 transition hover:scale-[1.01]"
              >
                {member ? 'Save changes' : 'Add member'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

type FieldProps = {
  label: string
  value: string
  placeholder: string
  suffix?: string
  type?: 'text' | 'number'
  onChange: (value: string) => void
}

function Field({ label, value, placeholder, suffix, type = 'text', onChange }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-slate-700">{label}</span>
      <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 transition focus-within:border-violet-300 focus-within:bg-white focus-within:ring-4 focus-within:ring-violet-100">
        <input
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          className="w-full border-0 bg-transparent text-sm font-medium text-slate-900 outline-none placeholder:text-slate-400"
        />
        {suffix ? <span className="text-sm font-bold text-slate-500">{suffix}</span> : null}
      </div>
    </label>
  )
}