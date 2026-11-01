from django import forms
from .models import Reminder


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = [
            'days_before',
            'notify_at',
            'active',
        ]
        labels = {
            'days_before': 'Dias de antecedência',
            'notify_at': 'Hora da notificação',
            'active': 'Ativo',
        }
        widgets = {
            'days_before': forms.NumberInput(attrs={
                'min': '0',
                'max': '365',
                'value': '1',
                'class': 'bg-[var(--field)] w-full text-[var(--ink)] rounded-field border border-[var(--line-field)] px-4 py-3 text-base sm:text-[15px] transition-colors placeholder:text-[var(--muted)] outline-none focus:border-brand focus:shadow-focus',
                'placeholder': 'Quantos dias antes?'
            }),
            'notify_at': forms.TimeInput(attrs={
                'type': 'time',
                'value': '09:00',
                'class': 'bg-[var(--field)] w-full text-[var(--ink)] rounded-field border border-[var(--line-field)] px-4 py-3 text-base sm:text-[15px] transition-colors placeholder:text-[var(--muted)] outline-none focus:border-brand focus:shadow-focus'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 accent-brand rounded'
            }),
        }
