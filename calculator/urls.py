from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/calculate/', views.CalculateAPIView.as_view(), name='api-calculate'),
    path('api/sample-data/', views.sample_data_view, name='api-sample-data'),
]
