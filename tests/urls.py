from django.urls import path

from . import views

urlpatterns = [
    path('images/new/', views.image_upload, name='image-upload'),
    path('images/<int:pk>/', views.image_detail, name='image-detail'),
]
