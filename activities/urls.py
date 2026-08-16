from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.activity_hub_view, name='activity_hub'),
    path('upload/', views.upload_activity_certificate_view, name='upload_certificate'),
    path('category/<str:category_code>/', views.category_detail_view, name='category_detail'),
    path('certificates/<int:cert_id>/review/', views.review_activity_cert_view, name='review_certificate'),
]
