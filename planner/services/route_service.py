import requests
import json
import polyline
import math


class RouteService:
    def __init__(self):
        # Using OpenRouteService free and alternative frim Google Maps
        self.api_key = "5b3ce3597851110001cf62480daa8adef8134bfd9c80a94b60a9b1da"  # Get from https://openrouteservice.org/
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    def get_coordinates(self, location):
        """Convert address to coordinates using OpenRouteService geocoding API"""
        geocode_url = "https://api.openrouteservice.org/geocode/search"
        params = {"api_key": self.api_key, "text": location}
        response = requests.get(geocode_url, params=params)
        data = response.json()

        if "features" in data and len(data["features"]) > 0:
            # Get the first result's coordinates (longitude, latitude)
            coords = data["features"][0]["geometry"]["coordinates"]
            return coords
        return None

    def calculate_route(self, origin, destination):
        """Calculate route between two 
        NB: OPen service only provides distance of less 6000km apart on free tier
        """
        origin_coords = self.get_coordinates(origin)
        dest_coords = self.get_coordinates(destination)

        if not origin_coords or not dest_coords:
            return None

        params = {
            "api_key": self.api_key,
            "start": f"{origin_coords[0]}, {origin_coords[1]}",
            "end": f"{dest_coords[0]}, {dest_coords[1]}",
        }

        headers = {
            "Accept": "application/json, application/geo+json, application/gpx+xml",
            "Content-Type": "application/json; charset=utf-8",
        }

        response = requests.get(self.base_url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    def calculate_trip_details(
        self, current_location, pickup_location, dropoff_location, current_cycle_used
    ):
        """Calculate the full trip with"""
        # Get route to pickup
        to_pickup = self.calculate_route(current_location, pickup_location)

        # Get route from pickup to dropoff
        pickup_to_dropoff = self.calculate_route(pickup_location, dropoff_location)
      
        # Process routes and calculate required stops
        return {
            "to_pickup": to_pickup,
            "pickup_to_dropoff": pickup_to_dropoff,
            "total_distance": self._calculate_total_distance(
                to_pickup, pickup_to_dropoff
            ),
            "total_duration": self._calculate_total_duration(
                to_pickup, pickup_to_dropoff
            ),
            "stops": self._calculate_required_stops(
                to_pickup, pickup_to_dropoff, current_cycle_used
            ),
        }

    def _calculate_total_distance(self, route1, route2):
        """Calculate total distance of the routes in miles"""
        if not route1 or not route2:
            return 0

        distance1 = (
            route1["routes"][0]["summary"]["distance"] if "routes" in route1 else 0
        )
        distance2 = (
            route2["routes"][0]["summary"]["distance"] if "routes" in route2 else 0
        )

        # Convert from meters to miles since US uses miles but we can use KM depending on location LOL
        return (distance1 + distance2) * 0.000621371

    def _calculate_total_duration(self, route1, route2):
        """Calculate total duration of the routes in hours"""
        if not route1 or not route2:
            return 0

        duration1 = (
            route1["routes"][0]["summary"]["duration"] if "routes" in route1 else 0
        )
        duration2 = (
            route2["routes"][0]["summary"]["duration"] if "routes" in route2 else 0
        )

        # Convert from seconds to hours
        return (duration1 + duration2) / 3600

    def _calculate_required_stops(self, route1, route2, current_cycle_used):
        """Calculate required stops based on HOS regulations"""
        total_duration = self._calculate_total_duration(route1, route2)
        total_distance = self._calculate_total_distance(route1, route2)

        # Add 1 hour each for pickup and dropoff
        total_duration += 2

        # Remaining drive time in the current cycle
        remaining_drive_time = 11 - current_cycle_used

        # Stops needed for 30-minute breaks (required after 8 hours of driving)
        thirty_min_breaks = math.floor(total_duration / 8)

        # Stops needed for 10-hour breaks (required after 11 hours of driving)
        ten_hour_breaks = math.ceil(
            max(0, (total_duration - remaining_drive_time)) / 11
        )

        # Stops needed for fueling (at least once every 1,000 miles)
        fuel_stops = math.floor(total_distance / 1000)

        stops = []

        # This is a simplified calculation - a real implementation would need to map these to specific
        # points along the route and calculate the exact timing

        return {
            "thirty_min_breaks": thirty_min_breaks,
            "ten_hour_breaks": ten_hour_breaks,
            "fuel_stops": fuel_stops,
        }
