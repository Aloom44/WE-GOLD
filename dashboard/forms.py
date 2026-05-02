from django import forms

from .models import AccountingEntry, Member, PrimaryLine, GlobalNote


class PrimaryLineForm(forms.ModelForm):
    class Meta:
        model = PrimaryLine
        fields = [
            'phone',
            'plan',
            'renewal_day',
            'plan_cost',
            'total_data',
            'total_minutes',
            'used_data',
            'used_minutes',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '01xxxxxxxxx'}),
            'plan': forms.Select(),
            'renewal_day': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['plan'].label = 'الباقة'
        self.fields['renewal_day'].label = 'يوم التجديد'
        self.fields['plan_cost'].label = 'تكلفة الباقة الشهرية'
        self.fields['total_data'].label = 'إجمالي الجيجات (GB)'
        self.fields['total_minutes'].label = 'إجمالي الدقائق'
        self.fields['used_data'].label = 'المستهلك من الجيجات (GB)'
        self.fields['used_minutes'].label = 'المستهلك من الدقائق'

        # Totals and usage are system-managed values.
        for field_name in ['total_data', 'total_minutes', 'used_data', 'used_minutes']:
            self.fields[field_name].disabled = True

        selected_plan = self.initial.get('plan') or getattr(self.instance, 'plan', None) or PrimaryLine.PLAN_525
        limits = PrimaryLine.PLAN_LIMITS.get(selected_plan, PrimaryLine.PLAN_LIMITS[PrimaryLine.PLAN_525])
        if self.instance and self.instance.pk:
            self.fields['total_data'].initial = self.instance.total_data
            self.fields['total_minutes'].initial = self.instance.total_minutes
            self.fields['used_data'].initial = self.instance.used_data
            self.fields['used_minutes'].initial = self.instance.used_minutes
            self.fields['plan_cost'].initial = self.instance.plan_cost
        else:
            self.fields['total_data'].initial = limits['data']
            self.fields['total_minutes'].initial = limits['minutes']
            self.fields['used_data'].initial = 0
            self.fields['used_minutes'].initial = 0
            self.fields['plan_cost'].initial = 0


class PrimaryLineRenewForm(forms.Form):
    carryover_data = forms.IntegerField(min_value=0, initial=0)
    carryover_minutes = forms.IntegerField(min_value=0, initial=0)

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line', None)
        super().__init__(*args, **kwargs)

        self.fields['carryover_data'].label = 'ترحيل الجيجات (GB)'
        self.fields['carryover_minutes'].label = 'ترحيل الدقائق'

        if self.line:
            self.fields['carryover_data'].initial = self.line.carryover_data
            self.fields['carryover_minutes'].initial = self.line.carryover_minutes

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'name',
            'phone',
            'data_allocation',
            'minute_allocation',
            'monthly_cost',
            'status',
            'note_type',
            'notes_text',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'اسم الفرد'}),
            'phone': forms.TextInput(attrs={'placeholder': '01xxxxxxxxx'}),
            'notes_text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'ملاحظة سريعة...'}),
        }

    def __init__(self, *args, **kwargs):
        self.line = kwargs.pop('line', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'الاسم'
        self.fields['phone'].label = 'رقم الهاتف'
        self.fields['data_allocation'].label = 'تخصيص الجيجات (GB)'
        self.fields['minute_allocation'].label = 'تخصيص الدقائق'
        self.fields['monthly_cost'].label = 'المبلغ المستحق (EGP)'
        self.fields['status'].label = 'حالة الدفع'
        self.fields['note_type'].label = 'نوع الملاحظة'
        self.fields['notes_text'].label = 'نص الملاحظة'

        # Payment status and Notes are operational; hide them from the main profile form.
        for field in ['status', 'note_type', 'notes_text']:
            if field in self.fields:
                del self.fields[field]

    def clean(self):
        cleaned_data = super().clean()
        line = self.line or getattr(self.instance, 'line', None)
        if not line:
            return cleaned_data

        data_allocation = cleaned_data.get('data_allocation')
        minute_allocation = cleaned_data.get('minute_allocation')

        if data_allocation is None or minute_allocation is None:
            return cleaned_data

        other_members = line.members.all()
        if self.instance and self.instance.pk:
            other_members = other_members.exclude(pk=self.instance.pk)

        other_data = sum(member.data_allocation for member in other_members)
        other_minutes = sum(member.minute_allocation for member in other_members)

        if other_data + data_allocation > line.total_data:
            self.add_error('data_allocation', 'تخصيص الجيجات يتجاوز المتاح في الباقة الأساسية.')

        if other_minutes + minute_allocation > line.total_minutes:
            self.add_error('minute_allocation', 'تخصيص الدقائق يتجاوز المتاح في الباقة الأساسية.')

        return cleaned_data


class AccountingEntryForm(forms.ModelForm):
    class Meta:
        model = AccountingEntry
        fields = ['title', 'amount', 'entry_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'عنوان الحركة'}),
            'entry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'ملاحظات اختيارية'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'العنوان'
        self.fields['amount'].label = 'المبلغ'
        self.fields['entry_date'].label = 'التاريخ'
        self.fields['notes'].label = 'ملاحظات'


class GlobalNoteForm(forms.ModelForm):
    class Meta:
        model = GlobalNote
        fields = [
            'title', 
            'content', 
            'note_type', 
            'priority', 
            'status', 
            'due_date', 
            'is_pinned', 
            'related_line', 
            'related_member'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'عنوان الملاحظة'}),
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'تفاصيل الملاحظة...'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'العنوان'
        self.fields['content'].label = 'الوصف'
        self.fields['note_type'].label = 'نوع الملاحظة'
        self.fields['priority'].label = 'الأولوية'
        self.fields['status'].label = 'الحالة'
        self.fields['due_date'].label = 'تاريخ الاستحقاق'
        self.fields['is_pinned'].label = 'تثبيت في الأعلى'
        self.fields['related_line'].label = 'ربط بخط (اختياري)'
        self.fields['related_member'].label = 'ربط بفرد (اختياري)'
