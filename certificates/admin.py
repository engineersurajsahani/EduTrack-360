from django.contrib import admin
from .models import Badge, StudentBadge, Certificate, DigitalNOC

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'icon', 'badge_color')

@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'awarded_at')
    search_fields = ('student__prn', 'badge__title')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'student', 'cert_type', 'score_percentage', 'issue_date', 'is_verified')
    list_filter = ('cert_type', 'is_verified')
    search_fields = ('certificate_id', 'student__prn', 'student__user__username')

@admin.register(DigitalNOC)
class DigitalNOCAdmin(admin.ModelAdmin):
    list_display = ('noc_id', 'student', 'purpose', 'is_approved', 'issued_at')
    list_filter = ('is_approved', 'library_clearance', 'academic_clearance', 'department_clearance', 'lab_clearance', 'fees_clearance')
    search_fields = ('noc_id', 'student__prn')
