from django.contrib import admin
from .models import StudentProfile

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'prn', 'roll_no', 'branch', 'semester', 'attendance_percentage')
    list_filter = ('branch', 'semester', 'academic_year')
    search_fields = ('prn', 'roll_no', 'user__first_name', 'user__last_name', 'user__username')
