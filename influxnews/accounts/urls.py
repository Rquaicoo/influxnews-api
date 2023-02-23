from django.urls import path
from .views import CreateUserAPIView

urlpatterns = [
    path('create-new-user/', CreateUserAPIView.as_view(), name='create-new-user'),
]