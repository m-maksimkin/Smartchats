from django import forms
from django.core.exceptions import ValidationError

from . import models


class AddTextFrom(forms.Form):
    chat_text = forms.CharField(
        max_length=10**5,
        widget=forms.Textarea(attrs={
            'class': 'textarea form-control',
            'rows': '13',
        }),
        required=False
    )


class ChatAddQuestionForm(forms.ModelForm):
    class Meta:
        model = models.ChatText
        fields = ['question', 'answer']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'textarea form-control',
                'rows': '2',
            }),
            'answer': forms.Textarea(attrs={
                'class': 'textarea form-control',
                'rows': '7',
            })
        }
        labels = {'question': 'Вопрос', 'answer': 'Ответ'}


ChatQuestionFormSet = forms.modelformset_factory(
    models.ChatText, form=ChatAddQuestionForm, extra=0,
)


class ChatCrawlUrlForm(forms.Form):
    crawl_url = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.example.com',
        })
    )
