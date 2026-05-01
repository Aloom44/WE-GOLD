from django.contrib import admin
from .models import AccountingEntry, Member, PrimaryLine


@admin.register(PrimaryLine)
class PrimaryLineAdmin(admin.ModelAdmin):
	list_display = ('phone', 'plan', 'plan_cost', 'renewal_day', 'carryover_data', 'carryover_minutes', 'total_data', 'total_minutes', 'used_data', 'used_minutes')
	search_fields = ('phone', 'plan')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
	list_display = ('name', 'phone', 'line', 'monthly_cost', 'status')
	list_filter = ('status', 'line')
	search_fields = ('name', 'phone')


@admin.register(AccountingEntry)
class AccountingEntryAdmin(admin.ModelAdmin):
	list_display = ('title', 'kind', 'amount', 'entry_date', 'system_key')
	list_filter = ('kind', 'entry_date')
	search_fields = ('title', 'notes')
