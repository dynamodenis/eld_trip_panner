from datetime import datetime, timedelta

class ELDService:
    def __init__(self):
        self.max_driving_hours = 11  # Maximum driving hours per day
        self.max_on_duty_hours = 14  # Maximum on-duty hours per day
        self.min_off_duty_hours = 10  # Minimum off-duty hours required
        self.max_weekly_hours = 70  # Maximum hours in 8 days (70-hour rule)
    
    def generate_log_sheets(self, trip_details, current_cycle_used):
        """Generate ELD log sheets for the entire trip"""
        total_duration = trip_details['total_duration']
        stops = trip_details['stops']
        
        # Start with current time as the beginning of the trip
        current_time = datetime.now()
        # Initialize cycle
        remaining_drive_time = self.max_driving_hours - current_cycle_used
        remaining_duty_time = self.max_on_duty_hours - current_cycle_used
        
        # Initialize logs
        log_sheets = []
        current_log = self._initialize_log_sheet(current_time.date())
        
        # Initial on-duty status the driver is going to pick up the load
    
        # Check if there is to pick up coordinate so that you drive and head to pick up location
        if len(trip_details['to_pickup']['features'][0]['geometry']['coordinates']) > 0:
            current_status = "D"
            current_log['events'].append({
                "time": current_time.strftime("%H:%M"),
                "status": current_status,
                "location": trip_details['to_pickup']['features'][0]['geometry']['coordinates'][0] if 'to_pickup' in trip_details else "Unknown"
            })
            
        # Get both drop off location and pick up location duration taken
        pickup_location_duration = (trip_details['to_pickup']['features'][0]['properties']['summary']['duration'] / 3600) if 'to_pickup' in trip_details else 0
        dropoff_location_duration = (trip_details['pickup_to_dropoff']['features'][0]['properties']['summary']['duration'] / 3600) if 'pickup_to_dropoff' in trip_details else 0
                
        # Simulate the trip hour by hour
        hours_simulated = 0
        pickup_location_hours = 0
        while hours_simulated < total_duration:
            # CHeck if pickup location has been reached
            if hours_simulated < pickup_location_duration:
                updated_time = current_time + timedelta(hours=pickup_location_duration)
                current_time += timedelta(hours=pickup_location_duration)
                # Add pickup
                current_status = "ON"
                current_log['events'].append({
                    "time": updated_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": trip_details['pickup_to_dropoff']['features'][0]['geometry']['coordinates'][0] if 'pickup_to_dropoff' in trip_details else "Unknown",
                    "remarks": "Pickup location"
                })
                
                current_time += timedelta(hours=1)
                
                current_status = "D"
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": trip_details['pickup_to_dropoff']['features'][0]['geometry']['coordinates'][0] if 'pickup_to_dropoff' in trip_details else "Unknown",
                })
                
            hours_simulated += 1               
            current_time += timedelta(hours=1)
            
            # Check if we need to start a new day
            if current_time.date() != datetime.strptime(current_log['date'], "%Y-%m-%d").date():
                log_sheets.append(current_log)
                current_log = self._initialize_log_sheet(current_time.date())
            
            # Update remaining times
            remaining_drive_time -= 1
            remaining_duty_time -= 1
            
            # Check if we need a 30-minute break
            if hours_simulated % 8 == 0:
                current_status = "OFF"
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": "Break location",
                    "remarks": "30-minute break"
                })
                
                # Add the break time
                current_time += timedelta(minutes=30)
                
                # Back to driving
                current_status = "D"
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": "Break location"
                })
            
            # Check if we need a 10-hour break
            if remaining_drive_time <= 0 or remaining_duty_time <= 0:
                current_status = "SB"  # Sleeper berth
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": "Rest location",
                    "remarks": "10-hour rest period"
                })
                
                # Add the rest time
                current_time += timedelta(hours=10)
                
                # Reset counters
                remaining_drive_time = self.max_driving_hours
                remaining_duty_time = self.max_on_duty_hours
                
                # Check if we need to start a new day
                if current_time.date() != datetime.strptime(current_log['date'], "%Y-%m-%d").date():
                    log_sheets.append(current_log)
                    current_log = self._initialize_log_sheet(current_time.date())
                
                # Back to driving
                current_status = "D"
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": "Rest location"
                })
            
            # Check for fuel stops
            if trip_details['stops']['fuel_stops']["number_of_fuel_stops"] > 0 and hours_simulated % (total_duration / (trip_details['stops']['fuel_stops']["number_of_fuel_stops"] + 1)) < 1:
                current_status = "ON"
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": "Fuel stop",
                    "remarks": "Fueling"
                })
                
                # Add fueling time
                current_time += timedelta(minutes=30)
                
                # Back to driving
                current_status = "D"
                current_log['events'].append({
                    "time": current_time.strftime("%H:%M"),
                    "status": current_status,
                    "location": "Fuel stop"
                })
        
        # Add the final dropoff
        current_time = current_time + timedelta(hours=total_duration-hours_simulated)
        
        current_status = "ON"
        current_log['events'].append({
            "time": current_time.strftime("%H:%M"),
            "status": current_status,
            "location": trip_details['pickup_to_dropoff']['features'][0]['geometry']['coordinates'][-1] if 'pickup_to_dropoff' in trip_details else "Unknown", # Get the last coordinate to represent final destination, wish there was an easier way
            "remarks": "Dropoff location"
        })
        
        # Add the final log sheet
        log_sheets.append(current_log)
        
        return log_sheets
    
    def _initialize_log_sheet(self, date):
        """Initialize a new log sheet for a given date"""
        return {
            "date": date.strftime("%Y-%m-%d"),
            "events": [],
            "grid": self._initialize_grid()
        }
    
    def _initialize_grid(self):
        """Initialize the grid for the ELD graph"""
        # Create a 24-hour grid with 15-minute intervals
        grid = []
        for hour in range(24):
            for minute in range(0, 60, 15):
                grid.append({
                    "time": f"{hour:02}:{minute:02}",
                    "status": None  # Will be filled in based on events
                })
        return grid