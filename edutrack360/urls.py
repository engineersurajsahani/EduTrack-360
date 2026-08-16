from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('academics/', include('academics.urls')),
    path('activities/', include('activities.urls')),
    path('certificates/', include('certificates.urls')),
    path('student/', include('students.urls')),
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=False)),
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),
    path('', include('dashboard.urls')),
    
    # Serve media files (QR codes, certificates, submissions) across environments
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
