from django.urls import path
from . import views

urlpatterns = [
  path('eval', views.eval, name='eval')
]