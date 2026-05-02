from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.management import call_command
from django.http import HttpResponse

from .forms import AccountingEntryForm, MemberForm, PrimaryLineForm, PrimaryLineRenewForm
from .models import AccountingEntry, Member, MemberNote, PrimaryLine, FinancialTransaction


def _ratio(part, whole):
    if whole <= 0:
        return 0
    return round((part / whole) * 100)


def _financial_summary(entries, kind):
    return entries.filter(kind=kind, system_key__isnull=True).aggregate(total=Sum('amount'))['total'] or 0


def accounting(request):
    today = timezone.localdate()
    
    # Financial queries using the new ledger
    ledger = FinancialTransaction.objects.all()
    current_ledger = ledger.filter(month=today.month, year=today.year)

    def get_total(qs, kind):
        return qs.filter(kind=kind).aggregate(total=Sum('amount'))['total'] or 0

    current_income = get_total(current_ledger, FinancialTransaction.KIND_INCOME)
    current_expense = get_total(current_ledger, FinancialTransaction.KIND_EXPENSE)
    current_net = current_income - current_expense

    overall_income = get_total(ledger, FinancialTransaction.KIND_INCOME)
    overall_expense = get_total(ledger, FinancialTransaction.KIND_EXPENSE)
    overall_net = overall_income - overall_expense

    income_form = AccountingEntryForm(prefix='income')
    expense_form = AccountingEntryForm(prefix='expense')

    context = {
        'income_form': income_form,
        'expense_form': expense_form,
        'current_income': current_income,
        'current_expense': current_expense,
        'current_net': current_net,
        'overall_income': overall_income,
        'overall_expense': overall_expense,
        'overall_net': overall_net,
        'recent_entries': ledger[:15], # Show ledger entries now
        'page_title': 'المحاسبة',
    }
    return render(request, 'dashboard/accounting.html', context)


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


def home(request):
    today = timezone.localdate()
    lines = list(PrimaryLine.objects.prefetch_related('members').order_by('id'))
    
    # Calculate per-line financial summary for the current month
    for line in lines:
        line_ledger = FinancialTransaction.objects.filter(line=line, month=today.month, year=today.year)
        line.current_revenue = line_ledger.filter(kind=FinancialTransaction.KIND_INCOME).aggregate(total=Sum('amount'))['total'] or 0
        line.current_cost = line_ledger.filter(kind=FinancialTransaction.KIND_EXPENSE).aggregate(total=Sum('amount'))['total'] or 0
        line.current_profit = line.current_revenue - line.current_cost

    context = {
        'lines': lines,
        'total_primary_lines': len(lines),
        'total_data': sum(line.total_data for line in lines),
        'total_minutes': sum(line.total_minutes for line in lines),
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


def run_migrations(request):
    """Temporary view to run migrations on Vercel."""
    try:
        call_command('migrate', interactive=False)
        return HttpResponse("✅ Migrations completed successfully!")
    except Exception as e:
        return HttpResponse(f"❌ Migration failed: {str(e)}", status=500)
