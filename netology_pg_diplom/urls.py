"""
URL configuration for netology_pg_diplom project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from backend.views import YamlUploadView, ProductInfoViewSet, RegisterUser, \
    BasketViewSet, ConfirmOrderViewset, OrderViewSet, AccountViewset

r = DefaultRouter()
r.register('products', ProductInfoViewSet)
r.register('basket', BasketViewSet)
r.register("confirm_order", ConfirmOrderViewset)
r.register('orders', OrderViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('yamlupload/', YamlUploadView.as_view()),
    path('auth/', include('rest_framework.urls')),
    path('get_token/', obtain_auth_token),
    path('register/', RegisterUser.as_view()),
    path('__debug__/', include(debug_toolbar.urls)),
    path('myaccount/', AccountViewset.as_view()),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('', include('social_django.urls')),
    path('silk/', include('silk.urls', namespace='silk')),
] + r.urls
