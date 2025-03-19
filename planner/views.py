from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TripInputSerializer, TripSerializer
from .models import Trip
from .services.route_service import RouteService
from .services.eld_service import ELDService

class TripPlannerView(APIView):
    def post(self, request):
        serializer = TripInputSerializer(data=request.data)
        if serializer.is_valid():
            # Save trip to database
            trip_data = Trip.objects.create(
                current_location=serializer.validated_data['current_location'],
                pickup_location=serializer.validated_data['pickup_location'],
                dropoff_location=serializer.validated_data['dropoff_location'],
                current_cycle_used=serializer.validated_data['current_cycle_used']
            )
            print(f"trip_data {trip_data}")
            # Calculate route and the ditances and time required
            route_service = RouteService()
            trip_details = route_service.calculate_trip_details(
                serializer.validated_data['current_location'],
                serializer.validated_data['pickup_location'],
                serializer.validated_data['dropoff_location'],
                serializer.validated_data['current_cycle_used']
            )
            # Generate trip logs
            eld_service = ELDService()
            log_sheets = eld_service.generate_log_sheets(
                trip_details,
                serializer.validated_data['current_cycle_used']
            )
            
            return Response({
                'trip': TripSerializer(trip_data).data,
                'route': trip_details,
                'log_sheets': log_sheets
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)