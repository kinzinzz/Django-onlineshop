from django.urls import path
from .views import * 

app_name = 'coupon'

urlpatterns = [
    path('add/', add_coupon, name='add'),
]