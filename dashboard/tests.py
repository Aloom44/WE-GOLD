from django.test import TestCase
from django.urls import reverse

from .models import AccountingEntry, Member, PrimaryLine


class PrimaryLineRenewalTests(TestCase):
	def setUp(self):
		self.line = PrimaryLine.objects.create(
			phone='01000000000',
			plan=PrimaryLine.PLAN_525,
			renewal_day=PrimaryLine.RENEWAL_DAY_1,
		)
		Member.objects.create(
			line=self.line,
			name='Member A',
			phone='01111111111',
			data_allocation=10,
			minute_allocation=500,
			amount_due=100,
			amount_paid=50,
		)
		self.line.refresh_from_db()

	def test_renewal_adds_carryover_to_current_line(self):
		response = self.client.post(
			reverse('line_renew', args=[self.line.id]),
			{
				'carryover_data': 7,
				'carryover_minutes': 300,
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.line.refresh_from_db()
		self.assertEqual(self.line.carryover_data, 7)
		self.assertEqual(self.line.carryover_minutes, 300)
		self.assertEqual(self.line.total_data, 37)
		self.assertEqual(self.line.total_minutes, 4000)
		self.assertEqual(self.line.used_data, 0)
		self.assertEqual(self.line.used_minutes, 0)

		member = self.line.members.first()
		self.assertIsNotNone(member)
		self.assertEqual(member.name, 'Member A')
		self.assertEqual(member.phone, '01111111111')
		self.assertEqual(member.data_allocation, 0)
		self.assertEqual(member.minute_allocation, 0)
		self.assertEqual(member.amount_due, 0)
		self.assertEqual(member.amount_paid, 0)
		self.assertEqual(member.status, Member.STATUS_UNPAID)

	def test_renewal_without_carryover_keeps_base_capacity(self):
		response = self.client.post(
			reverse('line_renew', args=[self.line.id]),
			{
				'carryover_data': 0,
				'carryover_minutes': 0,
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.line.refresh_from_db()
		self.assertEqual(self.line.carryover_data, 0)
		self.assertEqual(self.line.carryover_minutes, 0)
		self.assertEqual(self.line.total_data, 30)
		self.assertEqual(self.line.total_minutes, 3700)


class AccountingTests(TestCase):
	def test_primary_line_creates_system_expense_entry(self):
		line = PrimaryLine.objects.create(
			phone='01000000001',
			plan=PrimaryLine.PLAN_775,
			renewal_day=PrimaryLine.RENEWAL_DAY_16,
			plan_cost=450,
		)

		entry = AccountingEntry.objects.get(system_key=f'line-{line.id}')
		self.assertEqual(entry.kind, AccountingEntry.ENTRY_EXPENSE)
		self.assertEqual(entry.amount, 450)
		self.assertIn('تكلفة الباقة', entry.title)

	def test_accounting_page_accepts_manual_expense(self):
		response = self.client.post(
			reverse('accounting_expense_create'),
			{
				'expense-title': 'إعلان ممول',
				'expense-amount': 120,
				'expense-entry_date': '2026-04-12',
				'expense-notes': 'حملة شهرية',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'إعلان ممول')
		self.assertContains(response, '120')
