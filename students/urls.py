from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('profile/', views.student_profile_view, name='profile'),
    path('id-card/', views.digital_id_card_view, name='digital_id_card'),
    path('id-card/<int:student_id>/', views.digital_id_card_view, name='digital_id_card'),
    path('id-card-detail/<int:student_id>/', views.digital_id_card_view, name='digital_id_card_detail'),
    path('portfolio/', views.digital_portfolio_view, name='portfolio'),
    path('portfolio/<int:student_id>/', views.digital_portfolio_view, name='portfolio'),
    path('portfolio-detail/<int:student_id>/', views.digital_portfolio_view, name='portfolio_detail'),
    path('portfolio/prn/<str:prn>/', views.digital_portfolio_view, name='portfolio_by_prn'),
    path('qr/<uuid:qr_token>/', views.qr_student_progress_view, name='qr_progress_profile'),
    path('qr/<uuid:qr_token>/profile/', views.qr_student_progress_view, name='qr_progress'),
    path('search/', views.student_search_view, name='student_search'),
]
