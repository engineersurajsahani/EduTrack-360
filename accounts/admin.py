from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, FacultyProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('EduTrack 360 Role & Details', {'fields': ('role', 'phone', 'avatar', 'department')}),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'designation', 'qualification', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
