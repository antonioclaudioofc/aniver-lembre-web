from django import forms
from .models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'birthday', 'relationship', 'notes']
        labels = {
            'name': 'Nome',
            'birthday': 'Data de Nascimento',
            'relationship': 'Grau de Parentesco',
            'notes': 'Observações',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-[var(--field)] w-full text-[var(--ink)] rounded-field border border-[var(--line-field)] px-4 py-3 text-base sm:text-[15px] transition-colors placeholder:text-[var(--muted)] outline-none focus:border-brand focus:shadow-focus',
                'placeholder': 'Digite o nome do contato'
            }),
            'birthday': forms.DateInput(attrs={
                'type': 'date',
                'class': 'bg-[var(--field)] w-full text-[var(--ink)] rounded-field border border-[var(--line-field)] px-4 py-3 text-base sm:text-[15px] transition-colors placeholder:text-[var(--muted)] outline-none focus:border-brand focus:shadow-focus'
            }),
            'relationship': forms.TextInput(attrs={
                'class': 'bg-[var(--field)] w-full text-[var(--ink)] rounded-field border border-[var(--line-field)] px-4 py-3 text-base sm:text-[15px] transition-colors placeholder:text-[var(--muted)] outline-none focus:border-brand focus:shadow-focus',
                'placeholder': 'Ex: Amigo, Família, Colega...'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'bg-[var(--field)] w-full text-[var(--ink)] rounded-field border border-[var(--line-field)] px-4 py-3 text-base sm:text-[15px] transition-colors placeholder:text-[var(--muted)] outline-none focus:border-brand focus:shadow-focus resize-none',
                'placeholder': 'Adicione informações extras sobre o contato...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        birthday = cleaned_data.get('birthday')

        if not name:
            self.add_error('name', 'O nome é obrigatório.')

        if not birthday:
            self.add_error('birthday', 'A data de nascimento é obrigatória.')

        if birthday and birthday > forms.fields.datetime.date.today():
            self.add_error(
                'birthday', 'A data de nascimento não pode ser no futuro.')

        return cleaned_data
