from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.redirect_view, name='redirect_view'),
    path('student/', views.student_dashboard_view, name='student_dashboard'),
    path('faculty/', views.faculty_dashboard_view, name='faculty_dashboard'),
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('qr-scanner/', views.qr_scanner_view, name='qr_scanner'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('export/excel/', views.export_excel_view, name='export_excel'),
]
