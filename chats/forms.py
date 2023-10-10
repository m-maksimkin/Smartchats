from django import forms
from . import models


class AddTextFrom(forms.Form):
    chat_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea form-control',
            'rows': '13',
        }),
        required=False
    )
