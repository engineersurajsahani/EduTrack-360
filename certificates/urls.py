from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('', views.my_certificates_view, name='my_certificates'),
    path('verify/<uuid:cert_uuid>/', views.public_verify_certificate_view, name='verify_certificate'),
    path('download/<str:cert_id>/', views.download_certificate_pdf_view, name='download_certificate_pdf'),
    
    # NOC endpoints
    path('noc/', views.request_noc_view, name='request_noc'),
    path('noc/manage/', views.admin_noc_list_view, name='admin_noc_list'),
    path('noc/<int:noc_id>/update/', views.update_noc_clearance_view, name='update_noc_clearance'),
    path('noc/verify/<uuid:noc_uuid>/', views.public_verify_noc_view, name='verify_noc'),
    path('noc/download/<str:noc_id>/', views.download_noc_pdf_view, name='download_noc_pdf'),
]
