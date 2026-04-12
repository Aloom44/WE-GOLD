import { useMemo, useState } from 'react'
import {
  BoltIcon,
  ChartBarIcon,
  CreditCardIcon,
  SparklesIcon,
  UsersIcon,
} from '@heroicons/react/24/outline'
import { AllocationForm, type MemberDraft } from './components/AllocationForm'
import { MemberCard, type Member } from './components/MemberCard'
import { PrimaryLineCard } from './components/PrimaryLineCard'
import { ProgressBar } from './components/ProgressBar'
import type { MemberStatus } from './components/StatusBadge'
import { initialMembers, lines } from './data'

const getStatus = (amountPaid: number, amountDue: number): MemberStatus => {
  if (amountPaid >= amountDue) {
    return 'paid'
  }

  if (amountPaid > 0) {
    return 'partial'
  }

  return 'unpaid'
}

function App() {
  const [activeLineId, setActiveLineId] = useState(lines[0].id)
  const [membersByLine, setMembersByLine] = useState<Record<number, Member[]>>(() => initialMembers)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingMember, setEditingMember] = useState<Member | null>(null)

  const totalPrimaryLines = lines.length
  const totalFleetData = lines.reduce((sum, line) => sum + line.totalData, 0)
  const totalFleetMinutes = lines.reduce((sum, line) => sum + line.totalMinutes, 0)

  const activeLine = useMemo(
    () => lines.find((line) => line.id === activeLineId) ?? lines[0],
    [activeLineId],
  )

  const activeMembers = membersByLine[activeLine.id] ?? []

  const openAddMember = () => {
    setEditingMember(null)
    setIsFormOpen(true)
  }

  const openEditMember = (member: Member) => {
    setEditingMember(member)
    setIsFormOpen(true)
  }

  const closeForm = () => {
    setIsFormOpen(false)
    setEditingMember(null)
  }

  const saveMember = (draft: MemberDraft, memberId?: number) => {
    const member = {
      id: memberId ?? Date.now(),
      ...draft,
      status: getStatus(draft.amountPaid, draft.amountDue),
    }

    setMembersByLine((current) => {
      const lineMembers = current[activeLine.id] ?? []

      if (memberId) {
        return {
          ...current,
          [activeLine.id]: lineMembers.map((item) => (item.id === memberId ? member : item)),
        }
      }

      return {
        ...current,
        [activeLine.id]: [member, ...lineMembers],
      }
    })

    closeForm()
  }

  const deleteMember = (memberId: number) => {
    setMembersByLine((current) => ({
      ...current,
      [activeLine.id]: (current[activeLine.id] ?? []).filter((member) => member.id !== memberId),
    }))
  }

  const activeRemainingMinutes = activeLine.totalMinutes - activeLine.usedMinutes

  return (
    <div className="min-h-screen">
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
        <div className="overflow-hidden rounded-[1.5rem] border border-slate-900/10 bg-slate-950 px-4 py-3 text-white shadow-lg shadow-slate-900/10">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.3em] text-cyan-300/90">
                Primary Lines Overview
              </p>
              <p className="mt-1 text-sm font-medium text-white/80">
                Dashboard summary for all primary telecom lines.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs font-bold uppercase tracking-[0.16em] text-white/85">
              <span className="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/10">Fleet summary</span>
              <span className="rounded-full bg-cyan-400/15 px-3 py-1 text-cyan-200 ring-1 ring-cyan-300/20">
                Live management
              </span>
            </div>
          </div>
        </div>

        <header className="overflow-hidden rounded-[2rem] border border-white/70 bg-gradient-to-r from-[#6A1B9A] via-[#7B1FA2] to-[#9C27B0] text-white shadow-2xl shadow-purple-300/40">
          <div className="relative px-5 py-6 sm:px-8 sm:py-8">
            <div className="absolute inset-0 opacity-30">
              <div className="absolute -left-16 top-0 h-44 w-44 rounded-full bg-white/20 blur-3xl" />
              <div className="absolute right-0 top-10 h-56 w-56 rounded-full bg-fuchsia-200/20 blur-3xl" />
            </div>

            <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-2xl space-y-4">
                <span className="inline-flex w-fit items-center gap-2 rounded-full bg-white/15 px-4 py-2 text-xs font-bold uppercase tracking-[0.22em] text-white/90 ring-1 ring-white/15">
                  <SparklesIcon className="h-4 w-4" />
                  Premium Telecom Dashboard
                </span>
                <div>
                  <h1 className="text-4xl font-black tracking-tight sm:text-5xl">
                    باقات WE Gold
                  </h1>
                  <p className="mt-3 max-w-xl text-base font-medium text-white/85 sm:text-lg">
                    نظرة عامة على جميع الخطوط الأساسية والباقة الكلية ومتابعة الاستهلاك بشكل واضح وسريع.
                    Built for quick decisions on mobile and desktop.
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[520px]">
                <KpiCard
                  icon={UsersIcon}
                  label="Primary lines"
                  value={totalPrimaryLines.toString()}
                  note="network-wide lines"
                />
                <KpiCard
                  icon={ChartBarIcon}
                  label="Total data"
                  value={`${totalFleetData}GB`}
                  note="combined package capacity"
                />
                <KpiCard
                  icon={CreditCardIcon}
                  label="Total minutes"
                  value={`${totalFleetMinutes}`}
                  note="combined calling capacity"
                />
              </div>
            </div>
          </div>
        </header>

        <section className="space-y-5">
          <div className="flex flex-col gap-1">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-violet-500">
              Screen 1
            </p>
            <h2 className="text-2xl font-black tracking-tight text-slate-900">
              Dashboard - Primary Lines
            </h2>
          </div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {lines.map((line, index) => (
              <PrimaryLineCard
                key={line.id}
                line={line}
                selected={line.id === activeLine.id}
                onSelect={setActiveLineId}
                index={index}
              />
            ))}
          </div>
        </section>

        <section className="space-y-5">
          <div className="flex flex-col gap-1">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-violet-500">
              Screen 2
            </p>
            <h2 className="text-2xl font-black tracking-tight text-slate-900">
              Primary Line Details
            </h2>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1fr_1.05fr]">
            <div className="space-y-6">
              <article className="animate-card-in rounded-[2rem] border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.24em] text-violet-500">
                      Selected Line
                    </p>
                    <h3 className="mt-2 text-3xl font-black tracking-tight text-slate-900">
                      {activeLine.phone}
                    </h3>
                    <p className="mt-2 text-base font-semibold text-slate-500">
                      {activeLine.plan}
                    </p>
                  </div>

                  <div className="rounded-3xl bg-gradient-to-br from-[#6A1B9A] to-[#9C27B0] px-4 py-3 text-white shadow-lg shadow-purple-200/60">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/80">
                      Renewal Day
                    </p>
                    <p className="mt-1 text-2xl font-black">{activeLine.renewalDay}</p>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <InfoTile label="Plan Type" value={activeLine.plan} />
                  <InfoTile label="Total Data" value={`${activeLine.totalData}GB`} />
                  <InfoTile label="Total Minutes" value={`${activeLine.totalMinutes} min`} />
                </div>
              </article>

              <article className="animate-card-in rounded-[2rem] border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60" style={{ animationDelay: '80ms' }}>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.24em] text-violet-500">
                      Usage Card
                    </p>
                    <h3 className="mt-2 text-2xl font-black text-slate-900">Live package consumption</h3>
                  </div>
                  <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-bold text-slate-700">
                    Remaining highlighted
                  </div>
                </div>

                <div className="mt-5 grid gap-4">
                  <ProgressBar
                    label="Data usage"
                    used={activeLine.usedData}
                    total={activeLine.totalData}
                    unit="GB"
                    accent="purple"
                  />
                  <ProgressBar
                    label="Minutes usage"
                    used={activeLine.usedMinutes}
                    total={activeLine.totalMinutes}
                    unit=""
                    accent="emerald"
                  />
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <SummaryCard label="Used" value={`${activeLine.usedData}GB / ${activeLine.usedMinutes} min`} />
                  <SummaryCard label="Remaining" value={`${activeLine.totalData - activeLine.usedData}GB / ${activeRemainingMinutes} min`} accent />
                </div>
              </article>
            </div>

            <article className="animate-card-in rounded-[2rem] border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60" style={{ animationDelay: '140ms' }}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.24em] text-violet-500">
                    Members Section
                  </p>
                  <h3 className="mt-2 text-2xl font-black text-slate-900">Primary line members</h3>
                  <p className="mt-2 text-sm font-medium text-slate-500">
                    Each member is shown as a separate card with payment status and actions.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={openAddMember}
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[#6A1B9A] to-[#9C27B0] px-5 py-3 text-sm font-bold text-white shadow-lg shadow-purple-200 transition hover:scale-[1.01]"
                >
                  <BoltIcon className="h-4 w-4" />
                  Add Member
                </button>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2 2xl:grid-cols-1">
                {activeMembers.map((member, index) => (
                  <article key={member.id} className="animate-card-in" style={{ animationDelay: `${index * 70}ms` }}>
                    <MemberCard member={member} onEdit={openEditMember} onDelete={deleteMember} />
                  </article>
                ))}
              </div>
            </article>
          </div>
        </section>
      </main>

      <AllocationForm
        line={activeLine}
        isOpen={isFormOpen}
        member={editingMember}
        onClose={closeForm}
        onSubmit={saveMember}
      />
    </div>
  )
}

type KpiCardProps = {
  icon: typeof UsersIcon
  label: string
  value: string
  note: string
}

function KpiCard({ icon: Icon, label, value, note }: KpiCardProps) {
  return (
    <div className="rounded-3xl border border-white/15 bg-white/10 p-4 shadow-lg shadow-black/5 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-white/15 p-2.5">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white/75">{label}</p>
          <p className="mt-1 text-2xl font-black text-white">{value}</p>
        </div>
      </div>
      <p className="mt-3 text-sm font-medium text-white/75">{note}</p>
    </div>
  )
}

type InfoTileProps = {
  label: string
  value: string
}

function InfoTile({ label, value }: InfoTileProps) {
  return (
    <div className="rounded-3xl bg-slate-50 px-4 py-4 ring-1 ring-slate-200">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-base font-black text-slate-900">{value}</p>
    </div>
  )
}

type SummaryCardProps = {
  label: string
  value: string
  accent?: boolean
}

function SummaryCard({ label, value, accent }: SummaryCardProps) {
  return (
    <div className={`rounded-3xl px-4 py-4 ring-1 ${accent ? 'bg-violet-50 ring-violet-100' : 'bg-slate-50 ring-slate-200'}`}>
      <p className={`text-xs font-bold uppercase tracking-[0.18em] ${accent ? 'text-violet-500' : 'text-slate-500'}`}>
        {label}
      </p>
      <p className="mt-2 text-base font-black text-slate-900">{value}</p>
    </div>
  )
}

export default App
