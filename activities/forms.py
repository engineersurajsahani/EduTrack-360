from django import forms
from .models import ActivityCertificate, ActivityCategory

class ActivityCertificateUploadForm(forms.ModelForm):
    class Meta:
        model = ActivityCertificate
        fields = ['category', 'title', 'organization', 'event_date', 'level', 'achievement_role', 'certificate_file', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tree Plantation Drive / State Dance Competition / NPTEL Python Course'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MSBTE / IIT Bombay / Coursera / Rotary Club'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'achievement_role': forms.Select(attrs={'class': 'form-select'}),
            'certificate_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.png,.jpg,.jpeg'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of your role, outcomes, or learnings...'}),
        }


class ActivityCertificateReviewForm(forms.ModelForm):
    class Meta:
        model = ActivityCertificate
        fields = ['status', 'points_awarded', 'faculty_remark']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'points_awarded': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 50}),
            'faculty_remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Feedback or verification comments...'}),
        }
