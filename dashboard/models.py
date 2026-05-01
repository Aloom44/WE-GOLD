from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone


class PrimaryLine(models.Model):
	PLAN_525 = 'WE Gold 525'
	PLAN_775 = 'WE Gold 775'
	PLAN_1050 = 'WE Gold 1050'
	PLAN_1300 = 'WE Gold 1300'
	PLAN_2000 = 'WE Gold 2000'

	PLAN_CHOICES = [
		(PLAN_525, 'WE Gold 525'),
		(PLAN_775, 'WE Gold 775'),
		(PLAN_1050, 'WE Gold 1050'),
		(PLAN_1300, 'WE Gold 1300'),
		(PLAN_2000, 'WE Gold 2000'),
	]

	RENEWAL_DAY_1 = '1'
	RENEWAL_DAY_16 = '16'

	RENEWAL_DAY_CHOICES = [
		(RENEWAL_DAY_1, 'DAY1'),
		(RENEWAL_DAY_16, 'DAY16'),
	]

	PLAN_LIMITS = {
		PLAN_525: {'data': 30, 'minutes': 3700},
		PLAN_775: {'data': 60, 'minutes': 6000},
		PLAN_1050: {'data': 90, 'minutes': 8000},
		PLAN_1300: {'data': 110, 'minutes': 9000},
		PLAN_2000: {'data': 200, 'minutes': 10000},
	}

	phone = models.CharField(max_length=20, unique=True)
	plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default=PLAN_525)
	renewal_day = models.CharField(max_length=20, choices=RENEWAL_DAY_CHOICES, default=RENEWAL_DAY_1)
	plan_cost = models.PositiveIntegerField(default=0)
	carryover_data = models.PositiveIntegerField(default=0)
	carryover_minutes = models.PositiveIntegerField(default=0)
	total_data = models.PositiveIntegerField(default=30)
	total_minutes = models.PositiveIntegerField(default=3700)
	used_data = models.PositiveIntegerField(default=0)
	used_minutes = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['id']

	def clean(self):
		if self.plan not in self.PLAN_LIMITS:
			raise ValidationError({'plan': 'Invalid plan selected.'})
		if self.used_data > self.total_data:
			raise ValidationError({'used_data': 'Used data cannot exceed total data.'})
		if self.used_minutes > self.total_minutes:
			raise ValidationError({'used_minutes': 'Used minutes cannot exceed total minutes.'})

	def save(self, *args, **kwargs):
		limits = self.PLAN_LIMITS.get(self.plan)
		if limits:
			self.total_data = limits['data'] + self.carryover_data
			self.total_minutes = limits['minutes'] + self.carryover_minutes
		super().save(*args, **kwargs)
		AccountingEntry.sync_system_entry(
			system_key=f'line-{self.pk}',
			kind=AccountingEntry.ENTRY_EXPENSE,
			title=f'تكلفة الباقة - {self.phone}',
			amount=self.plan_cost,
			notes=f'الخط {self.phone} / {self.plan}',
		)

	def delete(self, *args, **kwargs):
		AccountingEntry.remove_system_entry(f'line-{self.pk}')
		super().delete(*args, **kwargs)

	def update_usage_from_members(self):
		aggregates = self.members.aggregate(
			used_data_sum=Sum('data_allocation'),
			used_minutes_sum=Sum('minute_allocation'),
		)
		self.used_data = aggregates['used_data_sum'] or 0
		self.used_minutes = aggregates['used_minutes_sum'] or 0
		self.save(update_fields=['carryover_data', 'carryover_minutes', 'used_data', 'used_minutes', 'total_data', 'total_minutes', 'updated_at'])

	@property
	def remaining_data(self):
		return max(self.total_data - self.used_data, 0)

	@property
	def remaining_minutes(self):
		return max(self.total_minutes - self.used_minutes, 0)

	@property
	def members_count(self):
		return self.members.count()

	@property
	def display_renewal_day(self):
		return f'DAY{self.renewal_day}'

	def __str__(self):
		return f'{self.phone} - {self.plan}'


class AccountingEntry(models.Model):
	ENTRY_INCOME = 'income'
	ENTRY_EXPENSE = 'expense'

	ENTRY_CHOICES = [
		(ENTRY_INCOME, 'Income'),
		(ENTRY_EXPENSE, 'Expense'),
	]

	kind = models.CharField(max_length=10, choices=ENTRY_CHOICES)
	title = models.CharField(max_length=120)
	amount = models.PositiveIntegerField(default=0)
	entry_date = models.DateField(default=timezone.localdate)
	notes = models.TextField(blank=True)
	system_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-entry_date', '-id']

	@classmethod
	def sync_system_entry(cls, system_key, kind, title, amount, notes=''):
		if amount <= 0:
			cls.objects.filter(system_key=system_key).delete()
			return

		cls.objects.update_or_create(
			system_key=system_key,
			defaults={
				'kind': kind,
				'title': title,
				'amount': amount,
				'notes': notes,
				'entry_date': timezone.localdate(),
			},
		)

	@classmethod
	def remove_system_entry(cls, system_key):
		cls.objects.filter(system_key=system_key).delete()

	def __str__(self):
		return f'{self.title} - {self.amount}'


class Member(models.Model):
	STATUS_PAID = 'paid'
	STATUS_UNPAID = 'unpaid'

	STATUS_CHOICES = [
		(STATUS_PAID, 'مدفوع'),
		(STATUS_UNPAID, 'غير مدفوع'),
	]

	NOTE_DELAYED = 'delayed'
	NOTE_CASH = 'cash'
	NOTE_FREE = 'free'
	NOTE_RELATIVE = 'relative'
	NOTE_CUSTOM = 'custom'

	NOTE_TYPE_CHOICES = [
		(NOTE_DELAYED, 'مؤجل'),
		(NOTE_CASH, 'دفع كاش'),
		(NOTE_FREE, 'مجاني'),
		(NOTE_RELATIVE, 'قريب'),
		(NOTE_CUSTOM, 'مخصص'),
	]

	line = models.ForeignKey(PrimaryLine, on_delete=models.CASCADE, related_name='members')
	name = models.CharField(max_length=80)
	phone = models.CharField(max_length=20)
	data_allocation = models.PositiveIntegerField(default=0)
	minute_allocation = models.PositiveIntegerField(default=0)
	monthly_cost = models.PositiveIntegerField(default=0)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_UNPAID)
	notes_text = models.TextField(blank=True)
	note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default=NOTE_CUSTOM, blank=True)

	class Meta:
		ordering = ['id']

	def clean(self):
		if not self.line_id:
			return

		other_members = Member.objects.filter(line_id=self.line_id)
		if self.pk:
			other_members = other_members.exclude(pk=self.pk)

		other_totals = other_members.aggregate(
			data_sum=Sum('data_allocation'),
			minutes_sum=Sum('minute_allocation'),
		)

		total_data_after = (other_totals['data_sum'] or 0) + self.data_allocation
		total_minutes_after = (other_totals['minutes_sum'] or 0) + self.minute_allocation

		errors = {}
		if total_data_after > self.line.total_data:
			errors['data_allocation'] = 'إجمالي تخصيص الجيجات للأفراد يتجاوز سعة الباقة الأساسية.'
		if total_minutes_after > self.line.total_minutes:
			errors['minute_allocation'] = 'إجمالي تخصيص الدقائق للأفراد يتجاوز سعة الباقة الأساسية.'

		if errors:
			raise ValidationError(errors)

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)
		self.line.update_usage_from_members()
		
		# Sync accounting based on status
		income_amount = self.monthly_cost if self.status == self.STATUS_PAID else 0
		AccountingEntry.sync_system_entry(
			system_key=f'member-{self.pk}',
			kind=AccountingEntry.ENTRY_INCOME,
			title=f'مدفوعات الأفراد - {self.name}',
			amount=income_amount,
			notes=f'الفرد {self.phone} على الخط {self.line.phone}',
		)

	def delete(self, *args, **kwargs):
		line = self.line
		AccountingEntry.remove_system_entry(f'member-{self.pk}')
		super().delete(*args, **kwargs)
		line.update_usage_from_members()

	def __str__(self):
		return f'{self.name} ({self.phone})'
