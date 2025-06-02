from django import forms
from .models import JobFeedback


class JobFeedbackForm(forms.ModelForm):
    class Meta:
        model = JobFeedback
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Leave your notes or feedback here...',
                'class': 'form-control'
            }),
        }
