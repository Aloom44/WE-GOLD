import type { Member } from './components/MemberCard'
import type { MemberStatus } from './components/StatusBadge'

export type Line = {
  id: number
  phone: string
  plan: string
  renewalDay: string
  totalData: number
  totalMinutes: number
  usedData: number
  usedMinutes: number
  membersCount: number
}

export const lines: Line[] = [
  {
    id: 1,
    phone: '0106 345 7812',
    plan: 'WE Gold 100',
    renewalDay: 'Day 1',
    totalData: 100,
    totalMinutes: 10000,
    usedData: 60,
    usedMinutes: 6200,
    membersCount: 8,
  },
  {
    id: 2,
    phone: '0111 902 4410',
    plan: 'WE Gold 100',
    renewalDay: 'Day 16',
    totalData: 100,
    totalMinutes: 10000,
    usedData: 42,
    usedMinutes: 4850,
    membersCount: 5,
  },
  {
    id: 3,
    phone: '0155 208 7781',
    plan: 'WE Gold 100',
    renewalDay: 'Day 1',
    totalData: 100,
    totalMinutes: 10000,
    usedData: 79,
    usedMinutes: 7300,
    membersCount: 11,
  },
  {
    id: 4,
    phone: '0122 509 6644',
    plan: 'WE Gold 100',
    renewalDay: 'Day 16',
    totalData: 100,
    totalMinutes: 10000,
    usedData: 55,
    usedMinutes: 5400,
    membersCount: 6,
  },
]

const deriveStatus = (amountPaid: number, amountDue: number): MemberStatus => {
  if (amountPaid >= amountDue) {
    return 'paid'
  }

  if (amountPaid > 0) {
    return 'partial'
  }

  return 'unpaid'
}

export const initialMembers: Record<number, Member[]> = {
  1: [
    {
      id: 101,
      name: 'Ahmed Hassan',
      phone: '0100 123 5678',
      dataAllocation: 10,
      minuteAllocation: 1000,
      amountDue: 50,
      amountPaid: 50,
      status: deriveStatus(50, 50),
    },
    {
      id: 102,
      name: 'Mona Samir',
      phone: '0109 221 4433',
      dataAllocation: 8,
      minuteAllocation: 800,
      amountDue: 50,
      amountPaid: 30,
      status: deriveStatus(30, 50),
    },
    {
      id: 103,
      name: 'Omar Adel',
      phone: '0101 778 9912',
      dataAllocation: 12,
      minuteAllocation: 1200,
      amountDue: 50,
      amountPaid: 0,
      status: deriveStatus(0, 50),
    },
  ],
  2: [
    {
      id: 201,
      name: 'Sara Nabil',
      phone: '0114 556 8890',
      dataAllocation: 10,
      minuteAllocation: 1000,
      amountDue: 60,
      amountPaid: 60,
      status: deriveStatus(60, 60),
    },
    {
      id: 202,
      name: 'Youssef Khaled',
      phone: '0110 334 7766',
      dataAllocation: 10,
      minuteAllocation: 1000,
      amountDue: 60,
      amountPaid: 40,
      status: deriveStatus(40, 60),
    },
  ],
  3: [
    {
      id: 301,
      name: 'Hend Tarek',
      phone: '0150 998 1122',
      dataAllocation: 14,
      minuteAllocation: 1200,
      amountDue: 70,
      amountPaid: 70,
      status: deriveStatus(70, 70),
    },
    {
      id: 302,
      name: 'Nour Ehab',
      phone: '0152 441 8891',
      dataAllocation: 8,
      minuteAllocation: 900,
      amountDue: 70,
      amountPaid: 0,
      status: deriveStatus(0, 70),
    },
    {
      id: 303,
      name: 'Salma Fathy',
      phone: '0155 700 2266',
      dataAllocation: 6,
      minuteAllocation: 700,
      amountDue: 70,
      amountPaid: 20,
      status: deriveStatus(20, 70),
    },
  ],
  4: [
    {
      id: 401,
      name: 'Hala Mostafa',
      phone: '0120 667 9001',
      dataAllocation: 10,
      minuteAllocation: 1000,
      amountDue: 55,
      amountPaid: 55,
      status: deriveStatus(55, 55),
    },
    {
      id: 402,
      name: 'Tamer Gamal',
      phone: '0121 334 1199',
      dataAllocation: 10,
      minuteAllocation: 900,
      amountDue: 55,
      amountPaid: 25,
      status: deriveStatus(25, 55),
    },
  ],
}