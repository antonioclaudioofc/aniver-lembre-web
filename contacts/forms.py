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
                'class': 'bg-white dark:bg-gray-800 w-full text-black dark:text-white rounded-md border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm transition-colors placeholder:text-gray-500 dark:placeholder:text-gray-500 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Digite o nome do contato'
            }),
            'birthday': forms.DateInput(attrs={
                'type': 'date',
                'class': 'bg-white dark:bg-gray-800 w-full text-black dark:text-white rounded-md border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm transition-colors placeholder:text-gray-500 dark:placeholder:text-gray-500 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'relationship': forms.TextInput(attrs={
                'class': 'bg-white dark:bg-gray-800 w-full text-black dark:text-white rounded-md border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm transition-colors placeholder:text-gray-500 dark:placeholder:text-gray-500 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Ex: Amigo, Família, Colega...'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'bg-white dark:bg-gray-800 w-full text-black dark:text-white rounded-md border border-gray-200 dark:border-gray-700 px-4 py-3 text-sm transition-colors placeholder:text-gray-500 dark:placeholder:text-gray-500 outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 resize-none',
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
