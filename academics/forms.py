from django import forms
from .models import Submission, SubjectTask, Subject

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submission_file', 'student_notes']
        widgets = {
            'submission_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.zip,.png,.jpg,.jpeg'}),
            'student_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional comments or github repository link...'}),
        }


class SubmissionReviewForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['status', 'marks_obtained', 'faculty_remark']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'faculty_remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Feedback or reason for approval/rejection...'}),
        }


class SubjectTaskForm(forms.ModelForm):
    class Meta:
        model = SubjectTask
        fields = ['subject', 'task_type', 'title', 'task_number', 'description', 'max_marks', 'due_date', 'attachment', 'is_required']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Assignment 1 - Network Layers'}),
            'task_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
