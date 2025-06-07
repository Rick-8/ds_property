from django import forms
from .models import JobFeedback


class JobFeedbackForm(forms.ModelForm):
    class Meta:
        model = JobFeedback
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'id': 'feedbackInput',
                'name': 'feedback',
                'class': 'form-control',
                'placeholder': 'Enter feedback here...',
            }),
        }
