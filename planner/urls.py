from django.urls import path
from .views import TripPlannerView

urlpatterns = [
    path('api/spotter-planner/', TripPlannerView.as_view(), name='spotter-planner'),
]