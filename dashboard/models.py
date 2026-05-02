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
		
		# Record automated line cost for current month
		now = timezone.localdate()
		FinancialTransaction.record(
			event_key=f"line-cost-{self.pk}-{now.month}-{now.year}",
			kind=FinancialTransaction.KIND_EXPENSE,
			amount=self.plan_cost,
			line=self,
			description=f"تكلفة باقة الخط {self.phone}",
			month=now.month,
			year=now.year
		)

	def delete(self, *args, **kwargs):
		# Cleanup transactions if needed, or keep for history
		super().delete(*args, **kwargs)

	def renew_line(self, carryover_data=0, carryover_minutes=0):
		"""Resets usage and records renewal expense for the NEXT month or current if late."""
		now = timezone.localdate()
		# For simplicity, we assume renewal is for the CURRENT month's billing cycle if called now
		# but if it's a 'renewal' action, it usually implies the start of a new period.
		
		# Reset member statuses
		self.members.update(status=Member.STATUS_UNPAID)
		
		# Update carryovers
		self.carryover_data = carryover_data
		self.carryover_minutes = carryover_minutes
		self.update_usage_from_members()
		
		# Record the renewal transaction
		FinancialTransaction.record(
			event_key=f"renewal-{self.pk}-{now.month}-{now.year}",
			kind=FinancialTransaction.KIND_EXPENSE,
			amount=self.plan_cost,
			line=self,
			description=f"تجديد باقة الخط {self.phone}",
			month=now.month,
			year=now.year
		)

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
		
		# Record automated income if paid
		now = timezone.localdate()
		event_key = f"member-pay-{self.pk}-{now.month}-{now.year}"
		
		if self.status == self.STATUS_PAID:
			FinancialTransaction.record(
				event_key=event_key,
				kind=FinancialTransaction.KIND_INCOME,
				amount=self.monthly_cost,
				line=self.line,
				member=self,
				description=f"تحصيل من {self.name} - خط {self.line.phone}",
				month=now.month,
				year=now.year
			)
		else:
			# If unpaid, ensure no income record exists for this month/event
			FinancialTransaction.objects.filter(event_key=event_key).delete()

	def delete(self, *args, **kwargs):
		line = self.line
		# We don't necessarily delete transactions on member delete to keep ledger history
		# but if it was for the current month, we might want to. 
		# For now, let's just delete the current month's automated entry if it exists.
		now = timezone.localdate()
		FinancialTransaction.objects.filter(event_key=f"member-pay-{self.pk}-{now.month}-{now.year}").delete()
		super().delete(*args, **kwargs)
		line.update_usage_from_members()

	def __str__(self):
		return f'{self.name} ({self.phone})'


class MemberNote(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notes')
	note_type = models.CharField(max_length=20, choices=Member.NOTE_TYPE_CHOICES, default=Member.NOTE_CUSTOM)
	text = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Note for {self.member.name} - {self.note_type}'


class FinancialTransaction(models.Model):
	KIND_INCOME = 'income'
	KIND_EXPENSE = 'expense'
	KIND_CHOICES = [(KIND_INCOME, 'إيراد'), (KIND_EXPENSE, 'مصروف')]

	CAT_AUTO = 'automated'
	CAT_MANUAL = 'manual'
	CAT_CHOICES = [(CAT_AUTO, 'آلي'), (CAT_MANUAL, 'يدوي')]

	kind = models.CharField(max_length=10, choices=KIND_CHOICES)
	category = models.CharField(max_length=10, choices=CAT_CHOICES, default=CAT_MANUAL)
	amount = models.PositiveIntegerField(default=0)
	line = models.ForeignKey(PrimaryLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
	member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
	
	month = models.PositiveSmallIntegerField()
	year = models.PositiveIntegerField()
	description = models.CharField(max_length=255)
	event_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
	is_reversed = models.BooleanField(default=False)
	
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	@classmethod
	def record(cls, event_key, kind, amount, description, month, year, category=CAT_AUTO, line=None, member=None):
		"""Idempotent transaction recording."""
		if amount <= 0:
			return None
		
		obj, created = cls.objects.update_or_create(
			event_key=event_key,
			defaults={
				'kind': kind,
				'category': category,
				'amount': amount,
				'description': description,
				'month': month,
				'year': year,
				'line': line,
				'member': member,
				'is_reversed': False
			}
		)
		return obj

	def __str__(self):
		return f"{self.get_kind_display()} - {self.amount} ({self.month}/{self.year})"


class GlobalNote(models.Model):
    TYPE_CHOICES = [
        ('reminder', 'تذكير'),
        ('collection', 'تحصيل'),
        ('expense', 'مصروف'),
        ('issue', 'مشكلة عميل'),
        ('followup', 'متابعة خط'),
        ('admin', 'إداري'),
        ('general', 'عام'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
        ('urgent', 'عاجل'),
    ]
    STATUS_CHOICES = [
        ('active', 'نشطة'),
        ('completed', 'مكتملة'),
        ('archived', 'مؤرشفة'),
    ]

    title = models.CharField(max_length=200, verbose_name="العنوان")
    content = models.TextField(verbose_name="الوصف")
    note_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general', verbose_name="النوع")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="الأولوية")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="الحالة")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    
    is_pinned = models.BooleanField(default=False, verbose_name="تثبيت")
    
    related_line = models.ForeignKey(PrimaryLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='global_notes', verbose_name="خط مرتبط")
    related_member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='global_notes', verbose_name="فرد مرتبط")

    class Meta:
        ordering = ['-is_pinned', '-priority', '-created_at']
        verbose_name = "ملاحظة عامة"
        verbose_name_plural = "الملاحظات العامة"

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and self.status == 'active':
            return self.due_date < timezone.localdate()
        return False
