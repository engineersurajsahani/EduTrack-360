from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('subjects/', views.subject_list_view, name='subject_list'),
    path('subjects/<int:subject_id>/', views.subject_detail_view, name='subject_detail'),
    path('tasks/<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('submissions/<int:submission_id>/review/', views.review_submission_view, name='review_submission'),
    path('submissions/history/', views.submission_history_view, name='submission_history'),
]
