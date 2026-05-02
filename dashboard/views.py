from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AccountingEntryForm, MemberForm, PrimaryLineForm, PrimaryLineRenewForm, GlobalNoteForm
from .models import AccountingEntry, Member, MemberNote, PrimaryLine, FinancialTransaction, GlobalNote
from django.contrib.auth.decorators import login_required


def notes_list(request):
    """Main notes dashboard with filtering."""
    notes = GlobalNote.objects.all()
    
    # Simple filtering
    prio = request.GET.get('priority')
    ntype = request.GET.get('type')
    status = request.GET.get('status', 'active')
    
    if prio: notes = notes.filter(priority=prio)
    if ntype: notes = notes.filter(note_type=ntype)
    if status: notes = notes.filter(status=status)
    
    form = GlobalNoteForm()
    
    context = {
        'notes': notes,
        'form': form,
        'priorities': GlobalNote.PRIORITY_CHOICES,
        'types': GlobalNote.TYPE_CHOICES,
        'statuses': GlobalNote.STATUS_CHOICES,
        'page_title': 'النوتة العامة',
    }
    return render(request, 'dashboard/notes.html', context)


def note_create(request):
    if request.method == 'POST':
        form = GlobalNoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('notes_list')
    return redirect('notes_list')


def note_toggle_pin(request, note_id):
    note = get_object_or_404(GlobalNote, id=note_id)
    note.is_pinned = not note.is_pinned
    note.save()
    return redirect(request.META.get('HTTP_REFERER', 'notes_list'))


def note_toggle_status(request, note_id, status):
    note = get_object_or_404(GlobalNote, id=note_id)
    if status in dict(GlobalNote.STATUS_CHOICES):
        note.status = status
        note.save()
    return redirect(request.META.get('HTTP_REFERER', 'notes_list'))


def note_delete(request, note_id):
    note = get_object_or_404(GlobalNote, id=note_id)
    if request.method == 'POST':
        note.delete()
    return redirect('notes_list')


def _ratio(part, whole):
    if whole <= 0:
        return 0
    return round((part / whole) * 100)


def _financial_summary(entries, kind):
    return entries.filter(kind=kind, system_key__isnull=True).aggregate(total=Sum('amount'))['total'] or 0


def accounting(request):
    today = timezone.localdate()
    
    # Global Financial queries
    ledger = FinancialTransaction.objects.all().order_by('-created_at')
    current_ledger = ledger.filter(month=today.month, year=today.year)

    def get_total(qs, kind):
        return qs.filter(kind=kind).aggregate(total=Sum('amount'))['total'] or 0

    current_income = get_total(current_ledger, FinancialTransaction.KIND_INCOME)
    current_expense = get_total(current_ledger, FinancialTransaction.KIND_EXPENSE)
    current_net = current_income - current_expense

    overall_income = get_total(ledger, FinancialTransaction.KIND_INCOME)
    overall_expense = get_total(ledger, FinancialTransaction.KIND_EXPENSE)
    overall_net = overall_income - overall_expense

    # Financial Transparency Lists
    current_income_list = current_ledger.filter(kind=FinancialTransaction.KIND_INCOME)
    current_expense_list = current_ledger.filter(kind=FinancialTransaction.KIND_EXPENSE)

    # Line Financial Analyzer Logic
    all_lines = PrimaryLine.objects.all()
    selected_line_id = request.GET.get('line_id')
    selected_line = None
    line_stats = {}
    line_recent_entries = []

    if selected_line_id:
        selected_line = get_object_or_404(PrimaryLine.objects.prefetch_related('members'), id=selected_line_id)
        line_ledger = ledger.filter(line=selected_line, month=today.month, year=today.year)
        
        rev = get_total(line_ledger, FinancialTransaction.KIND_INCOME)
        exp = get_total(line_ledger, FinancialTransaction.KIND_EXPENSE)
        
        m_total = selected_line.members.count()
        m_paid = selected_line.members.filter(status=Member.STATUS_PAID).count()
        
        line_stats = {
            'revenue': rev,
            'expense': exp,
            'net': rev - exp,
            'members_total': m_total,
            'members_paid': m_paid,
            'collection_rate': _ratio(m_paid, m_total),
        }
        line_recent_entries = ledger.filter(line=selected_line)[:10]

    income_form = AccountingEntryForm(prefix='income')
    expense_form = AccountingEntryForm(prefix='expense')

    context = {
        'income_form': income_form,
        'expense_form': expense_form,
        'current_income': current_income,
        'current_expense': current_expense,
        'current_net': current_net,
        'current_income_list': current_income_list,
        'current_expense_list': current_expense_list,
        'overall_income': overall_income,
        'overall_expense': overall_expense,
        'overall_net': overall_net,
        'recent_entries': ledger[:15],
        'all_lines': all_lines,
        'selected_line': selected_line,
        'line_stats': line_stats,
        'line_recent_entries': line_recent_entries,
        'urgent_notes_count': GlobalNote.objects.filter(status='active', priority='urgent').count(),
        'page_title': 'المحاسبة',
    }
    return render(request, 'dashboard/accounting.html', context)


def link_ledger_to_lines(request):
    """Clean and rebuild the ledger to fix duplicates and ensure accuracy."""
    import re
    today = timezone.localdate()
    
    # 1. CLEAR EXISTING LEDGER (Start Fresh to fix duplicates)
    FinancialTransaction.objects.all().delete()
    
    # 2. MIGRATE ONLY MANUAL/CUSTOM OLD ENTRIES
    # Automated ones will be handled by the new sync logic below
    old_manual_entries = AccountingEntry.objects.filter(system_key__isnull=True)
    for entry in old_manual_entries:
        FinancialTransaction.objects.create(
            kind=entry.kind,
            category=FinancialTransaction.CAT_MANUAL,
            amount=entry.amount,
            description=entry.title,
            month=entry.entry_date.month,
            year=entry.entry_date.year,
            created_at=entry.created_at
        )

    # 3. SYNC CURRENT MONTH AUTOMATED RECORDS
    # This ensures every line and paid member has exactly ONE record for May 2026
    synced_count = 0
    for line in PrimaryLine.objects.all():
        # Record line cost
        FinancialTransaction.record(
            event_key=f"line-cost-{line.pk}-{today.month}-{today.year}",
            kind=FinancialTransaction.KIND_EXPENSE,
            amount=line.plan_cost,
            line=line,
            description=f"تكلفة باقة الخط {line.phone}",
            month=today.month,
            year=today.year
        )
        synced_count += 1
        
        # Record member payments
        for member in line.members.filter(status=Member.STATUS_PAID):
            FinancialTransaction.record(
                event_key=f"member-pay-{member.pk}-{today.month}-{today.year}",
                kind=FinancialTransaction.KIND_INCOME,
                amount=member.monthly_cost,
                line=line,
                member=member,
                description=f"تحصيل من {member.name} - خط {line.phone}",
                month=today.month,
                year=today.year
            )
            synced_count += 1
                
    return HttpResponse(f"✅ Ledger cleaned and rebuilt! Synced {synced_count} automated records for the current month.")


def accounting_income_create(request):
    if request.method == 'POST':
        form = AccountingEntryForm(request.POST, prefix='income')
        if form.is_valid():
            today = timezone.localdate()
            FinancialTransaction.objects.create(
                kind=FinancialTransaction.KIND_INCOME,
                category=FinancialTransaction.CAT_MANUAL,
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data['title'],
                month=today.month,
                year=today.year
            )
            return redirect('accounting')
    return redirect('accounting')


def accounting_expense_create(request):
    if request.method == 'POST':
        form = AccountingEntryForm(request.POST, prefix='expense')
        if form.is_valid():
            today = timezone.localdate()
            FinancialTransaction.objects.create(
                kind=FinancialTransaction.KIND_EXPENSE,
                category=FinancialTransaction.CAT_MANUAL,
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data['title'],
                month=today.month,
                year=today.year
            )
            return redirect('accounting')
    return redirect('accounting')


def accounting_delete(request, entry_id):
    entry = get_object_or_404(FinancialTransaction, id=entry_id)
    if request.method == 'POST':
        entry.delete()
    return redirect('accounting')


from django.db import utils as db_utils
from django.core.management import call_command

def sync_global_notes():
    """Automated logic to create system reminders."""
    today = timezone.localdate()
    
    # 1. Approaching Renewals (within 3 days)
    for line in PrimaryLine.objects.all():
        renew_day_int = 1 if line.renewal_day == PrimaryLine.RENEWAL_DAY_1 else 16
        
        # Calculate next renewal date
        if today.day <= renew_day_int:
            renew_date = today.replace(day=renew_day_int)
        else:
            if today.month == 12:
                renew_date = today.replace(year=today.year+1, month=1, day=renew_day_int)
            else:
                renew_date = today.replace(month=today.month+1, day=renew_day_int)
        
        days_left = (renew_date - today).days
        if 0 <= days_left <= 3:
            GlobalNote.objects.get_or_create(
                title=f"تجديد خط {line.phone}",
                related_line=line,
                status='active',
                defaults={
                    'content': f"موعد تجديد الباقة للخط {line.phone} خلال {days_left} أيام (بتاريخ {renew_date.strftime('%d/%m')})",
                    'note_type': 'reminder',
                    'priority': 'high' if days_left > 1 else 'urgent',
                    'due_date': renew_date
                }
            )

    # 2. Unpaid Members (Collection warnings)
    for member in Member.objects.filter(status=Member.STATUS_UNPAID):
        line = member.line
        renew_day_int = 1 if line.renewal_day == PrimaryLine.RENEWAL_DAY_1 else 16
        
        # If it's past the renewal day of the current month
        if today.day > renew_day_int:
            GlobalNote.objects.get_or_create(
                title=f"تحصيل من {member.name}",
                related_member=member,
                status='active',
                defaults={
                    'content': f"العضو {member.name} لم يقم بالسداد لخط {line.phone} رغم مرور موعد التجديد (يوم {renew_day_int}).",
                    'note_type': 'collection',
                    'priority': 'medium'
                }
            )


def home(request):
    try:
        sync_global_notes()
    except db_utils.ProgrammingError:
        # Table might be missing on server (Vercel), try auto-migrating
        call_command('migrate', interactive=False)
        sync_global_notes()
    
    today = timezone.localdate()
    lines = list(PrimaryLine.objects.prefetch_related('members').order_by('id'))
    
    # Calculate per-line financial summary for the current month
    for line in lines:
        line_ledger = FinancialTransaction.objects.filter(line=line, month=today.month, year=today.year)
        line.current_revenue = line_ledger.filter(kind=FinancialTransaction.KIND_INCOME).aggregate(total=Sum('amount'))['total'] or 0
        line.current_cost = line_ledger.filter(kind=FinancialTransaction.KIND_EXPENSE).aggregate(total=Sum('amount'))['total'] or 0
        line.current_profit = line.current_revenue - line.current_cost

    # Fetch top 3 active notes for the widget
    recent_notes = GlobalNote.objects.filter(status='active')[:3]
    urgent_notes_count = GlobalNote.objects.filter(status='active', priority='urgent').count()

    context = {
        'lines': lines,
        'total_primary_lines': len(lines),
        'total_data': sum(line.total_data for line in lines),
        'total_minutes': sum(line.total_minutes for line in lines),
        'recent_notes': recent_notes,
        'urgent_notes_count': urgent_notes_count,
    }

    return render(request, 'dashboard/home.html', context)


def members(request, line_id):
    active_line = get_object_or_404(PrimaryLine.objects.prefetch_related('members'), id=line_id)
    active_members = active_line.members.all()

    data_total = active_line.total_data
    data_used = active_line.used_data
    data_remaining = active_line.remaining_data
    data_used_percentage = _ratio(data_used, data_total)
    data_remaining_percentage = _ratio(data_remaining, data_total)

    minutes_total = active_line.total_minutes
    minutes_used = active_line.used_minutes
    minutes_remaining = active_line.remaining_minutes
    minutes_used_percentage = _ratio(minutes_used, minutes_total)
    minutes_remaining_percentage = _ratio(minutes_remaining, minutes_total)

    context = {
        'active_line': active_line,
        'active_members': active_members,
        'total_primary_lines': PrimaryLine.objects.count(),
        'data_total': data_total,
        'data_used': data_used,
        'data_remaining': data_remaining,
        'data_used_percentage': data_used_percentage,
        'data_remaining_percentage': data_remaining_percentage,
        'minutes_total': minutes_total,
        'minutes_used': minutes_used,
        'minutes_remaining': minutes_remaining,
        'minutes_used_percentage': minutes_used_percentage,
        'minutes_remaining_percentage': minutes_remaining_percentage,
        'member_note_types': Member.NOTE_TYPE_CHOICES,
        'urgent_notes_count': GlobalNote.objects.filter(status='active', priority='urgent').count(),
    }

    return render(request, 'dashboard/members.html', context)


def line_create(request):
    if request.method == 'POST':
        form = PrimaryLineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PrimaryLineForm()

    return render(request, 'dashboard/line_form.html', {'form': form, 'page_title': 'إضافة خط أساسي'})


def line_update(request, line_id):
    line = get_object_or_404(PrimaryLine, id=line_id)

    if request.method == 'POST':
        form = PrimaryLineForm(request.POST, instance=line)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PrimaryLineForm(instance=line)

    return render(request, 'dashboard/line_form.html', {'form': form, 'page_title': 'تعديل الخط الأساسي', 'line': line})


def line_delete(request, line_id):
    line = get_object_or_404(PrimaryLine, id=line_id)
    if request.method == 'POST':
        line.delete()
    return redirect('home')


def line_renew(request, line_id):
    line = get_object_or_404(PrimaryLine.objects.prefetch_related('members'), id=line_id)

    if request.method == 'POST':
        form = PrimaryLineRenewForm(request.POST, line=line)
        if form.is_valid():
            line.renew_line(
                carryover_data=form.cleaned_data['carryover_data'],
                carryover_minutes=form.cleaned_data['carryover_minutes']
            )
            return redirect('home')
    else:
        form = PrimaryLineRenewForm(line=line)

    context = {
        'form': form,
        'line': line,
        'page_title': 'تجديد الخط الأساسي',
    }
    return render(request, 'dashboard/renew_form.html', context)


def member_create(request, line_id):
    line = get_object_or_404(PrimaryLine, id=line_id)

    if request.method == 'POST':
        form = MemberForm(request.POST, line=line)
        if form.is_valid():
            member = form.save(commit=False)
            member.line = line
            member.save()
            return redirect('members', line_id=line.id)
    else:
        form = MemberForm(line=line)

    context = {
        'form': form,
        'line': line,
        'page_title': 'إضافة فرد',
    }
    return render(request, 'dashboard/member_form.html', context)


def member_update(request, line_id, member_id):
    line = get_object_or_404(PrimaryLine, id=line_id)
    member = get_object_or_404(Member, id=member_id, line=line)

    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member, line=line)
        if form.is_valid():
            form.save()
            return redirect('members', line_id=line.id)
    else:
        form = MemberForm(instance=member, line=line)

    context = {
        'form': form,
        'line': line,
        'member': member,
        'page_title': 'تعديل بيانات الفرد',
    }
    return render(request, 'dashboard/member_form.html', context)


def member_delete(request, line_id, member_id):
    line = get_object_or_404(PrimaryLine, id=line_id)
    member = get_object_or_404(Member, id=member_id, line=line)
    if request.method == 'POST':
        member.delete()
    return redirect('members', line_id=line.id)


def member_payment_status_toggle(request, line_id, member_id):
    line = get_object_or_404(PrimaryLine, id=line_id)
    member = get_object_or_404(Member, id=member_id, line=line)
    
    if request.method == 'POST':
        if member.status == Member.STATUS_PAID:
            member.status = Member.STATUS_UNPAID
        else:
            member.status = Member.STATUS_PAID
        member.save()
        
    return redirect('members', line_id=line.id)


def member_note_add(request, line_id, member_id):
    line = get_object_or_404(PrimaryLine, id=line_id)
    member = get_object_or_404(Member, id=member_id, line=line)
    
    if request.method == 'POST':
        note_type = request.POST.get('note_type', Member.NOTE_CUSTOM)
        notes_text = request.POST.get('notes_text', '').strip()
        
        if notes_text or note_type != Member.NOTE_CUSTOM:
            MemberNote.objects.create(
                member=member,
                note_type=note_type,
                text=notes_text
            )
        
    return redirect('members', line_id=line.id)


def member_note_delete(request, line_id, note_id):
    note = get_object_or_404(MemberNote, id=note_id, member__line_id=line_id)
    if request.method == 'POST':
        note.delete()
        
    return redirect('members', line_id=line_id)
