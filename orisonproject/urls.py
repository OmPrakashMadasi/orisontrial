
from django.contrib import admin
from django.urls import path,include
from . import settings
from django.conf.urls.static import static
from webapp import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('webapp.urls')),
    path('', views.home)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
