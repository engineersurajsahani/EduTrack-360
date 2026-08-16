from django.contrib import admin
from .models import ActivityCategory, ActivityScheme, ActivityCertificate

@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'target_points', 'weight_percentage')

@admin.register(ActivityScheme)
class ActivitySchemeAdmin(admin.ModelAdmin):
    list_display = ('activity_name', 'category', 'default_points')
    list_filter = ('category',)

@admin.register(ActivityCertificate)
class ActivityCertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'title', 'level', 'achievement_role', 'status', 'points_awarded', 'event_date')
    list_filter = ('status', 'category', 'level', 'achievement_role')
    search_fields = ('student__prn', 'student__user__username', 'title')
