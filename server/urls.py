from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from myapp.views import *
from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="Rent Cars API",
        default_version='v1',
        description="API для аренды автомобилей",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

router = DefaultRouter()
router.register('cars', CarViewSet)
router.register('dogovors', DogovorViewSet, basename='dogovor')
router.register('messages', MessageViewSet, basename='message')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('', TemplateView.as_view(template_name='index.html')),
    path('', include(router.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)