from django.contrib import admin
from .models import Program, Branch, AcademicYear, Semester, Division, Subject, SubjectTask, Submission

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'duration_years')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'program', 'department')
    list_filter = ('program', 'department')

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'year_number', 'code')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('roman_name', 'number', 'academic_year')
    list_filter = ('academic_year',)

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'semester')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'semester', 'assigned_faculty', 'is_active')
    list_filter = ('branch', 'semester', 'is_active')
    search_fields = ('name', 'code')

@admin.register(SubjectTask)
class SubjectTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'task_type', 'task_number', 'max_marks', 'due_date')
    list_filter = ('task_type', 'subject__branch', 'subject__semester')
    search_fields = ('title', 'subject__name', 'subject__code')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'status', 'marks_obtained', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'task__task_type', 'task__subject')
    search_fields = ('student__prn', 'student__user__username', 'task__title')
