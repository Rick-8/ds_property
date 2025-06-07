from django import forms
from .models import JobFeedback

class JobFeedbackForm(forms.ModelForm):
    class Meta:
        model = JobFeedback
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'id': 'feedbackInput',
                'name': 'feedback',  # ensure it's named properly
                'class': 'form-control',
                'placeholder': 'Enter feedback here...',
            }),
        }