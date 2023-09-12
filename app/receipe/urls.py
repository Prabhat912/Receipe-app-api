"""
URL Mapping for receipe app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from receipe import views

router = DefaultRouter()

router.register('receipes', views.ReceipeViewSet)
router.register('tags', views.TagViewSet)

app_name = 'receipe'

urlpatterns = [
    path('', include(router.urls)),
]
