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
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from backend.views import CategoryViewSet, ShopViewSet, YamlUploadView, ProductInfoViewSet, RegisterUser, \
    ShoppingCartViewSet, ConfirmOrderViewset, OrderViewSet

r = DefaultRouter()
r.register('cat', CategoryViewSet)
r.register('shop', ShopViewSet)
r.register('products', ProductInfoViewSet)
r.register('shopping_cart', ShoppingCartViewSet)
r.register("confirm_order", ConfirmOrderViewset)
r.register('orders', OrderViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('yamlupload/', YamlUploadView.as_view()),
    #Путь для сессионной авторизации
    path('auth/', include('rest_framework.urls')),
    path('get_token/', obtain_auth_token),
    path('register/', RegisterUser.as_view())
] + r.urls
