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
                'class': 'bg-white dark:bg-gray-800 w-full text-black dark:text-white rounded-md border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm transition-colors placeholder:text-gray-500 dark:placeholder:text-gray-500 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Quantos dias antes?'
            }),
            'notify_at': forms.TimeInput(attrs={
                'type': 'time',
                'value': '09:00',
                'class': 'bg-white dark:bg-gray-800 w-full text-black dark:text-white rounded-md border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm transition-colors placeholder:text-gray-500 dark:placeholder:text-gray-500 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 border-gray-300 dark:border-gray-600 dark:bg-gray-800 rounded focus:ring-indigo-500 focus:ring-2'
            }),
        }
