from django.urls import path
from .views import TripPlannerView

urlpatterns = [
    path('api/spotter-panner/', TripPlannerView.as_view(), name='spotter-planner'),
]