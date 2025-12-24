"""
Cookie utility functions for RideON application
Handles user preferences, session data, and convenience features
"""

import json
from datetime import datetime, timedelta
from django.http import HttpResponse


class CookieManager:
    """Utility class for managing cookies in RideON application"""
    
    # Cookie names
    USER_PREFERENCES = 'rideon_preferences'
    RECENT_LOCATIONS = 'rideon_recent_locations'
    FAVORITE_ROUTES = 'rideon_favorite_routes'
    BOOKING_PREFERENCES = 'rideon_booking_prefs'
    LAST_VEHICLE_TYPE = 'rideon_last_vehicle'
    
    @staticmethod
    def set_cookie(response, key, value, max_age=None, expires=None):
        """
        Set a cookie with proper security settings
        """
        if max_age is None:
            max_age = 30 * 24 * 60 * 60  # 30 days default
            
        # Convert complex data to JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            
        response.set_cookie(
            key,
            value,
            max_age=max_age,
            expires=expires,
            httponly=False,  # Allow JavaScript access for frontend features
            secure=False,    # Set to True in production with HTTPS
            samesite='Lax'
        )
        return response
    
    @staticmethod
    def get_cookie(request, key, default=None):
        """
        Get cookie value with JSON parsing support
        """
        value = request.COOKIES.get(key, default)
        if value and value != default:
            try:
                # Try to parse as JSON
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value
        return default
    
    @staticmethod
    def delete_cookie(response, key):
        """
        Delete a cookie
        """
        response.delete_cookie(key)
        return response
    
    @staticmethod
    def set_user_preferences(response, preferences):
        """
        Store user preferences in cookies
        preferences = {
            'preferred_vehicle': 'Auto',
            'preferred_payment': 'wallet',
            'theme': 'light',
            'notifications': True
        }
        """
        return CookieManager.set_cookie(response, CookieManager.USER_PREFERENCES, preferences)
    
    @staticmethod
    def get_user_preferences(request):
        """
        Get user preferences from cookies
        """
        return CookieManager.get_cookie(request, CookieManager.USER_PREFERENCES, {
            'preferred_vehicle': 'Auto',
            'preferred_payment': 'wallet',
            'theme': 'light',
            'notifications': True
        })
    
    @staticmethod
    def add_recent_location(response, request, location_type, location):
        """
        Add location to recent locations list
        location_type: 'pickup' or 'destination'
        location: string location name
        """
        recent_locations = CookieManager.get_cookie(request, CookieManager.RECENT_LOCATIONS, {
            'pickup': [],
            'destination': []
        })
        
        # Ensure recent_locations is a dict and has the required keys
        if not isinstance(recent_locations, dict):
            recent_locations = {'pickup': [], 'destination': []}
        
        if location_type not in recent_locations:
            recent_locations[location_type] = []
        
        if location_type in recent_locations and isinstance(recent_locations[location_type], list):
            # Remove if already exists (to move to top)
            if location in recent_locations[location_type]:
                recent_locations[location_type].remove(location)
            
            # Add to beginning of list
            recent_locations[location_type].insert(0, location)
            
            # Keep only last 10 locations
            recent_locations[location_type] = recent_locations[location_type][:10]
        
        return CookieManager.set_cookie(response, CookieManager.RECENT_LOCATIONS, recent_locations)
    
    @staticmethod
    def get_recent_locations(request):
        """
        Get recent locations from cookies
        """
        return CookieManager.get_cookie(request, CookieManager.RECENT_LOCATIONS, {
            'pickup': [],
            'destination': []
        })
    
    @staticmethod
    def set_last_vehicle_type(response, vehicle_type):
        """
        Remember the last selected vehicle type
        """
        return CookieManager.set_cookie(response, CookieManager.LAST_VEHICLE_TYPE, vehicle_type)
    
    @staticmethod
    def get_last_vehicle_type(request):
        """
        Get the last selected vehicle type
        """
        return CookieManager.get_cookie(request, CookieManager.LAST_VEHICLE_TYPE, 'Auto')
    
    @staticmethod
    def add_favorite_route(response, request, pickup, destination):
        """
        Add a route to favorites
        """
        favorites = CookieManager.get_cookie(request, CookieManager.FAVORITE_ROUTES, [])
        
        # Ensure favorites is a list
        if not isinstance(favorites, list):
            favorites = []
        
        route = {'pickup': pickup, 'destination': destination, 'added_at': datetime.now().isoformat()}
        
        # Remove if already exists
        favorites = [f for f in favorites if not (f.get('pickup') == pickup and f.get('destination') == destination)]
        
        # Add to beginning
        favorites.insert(0, route)
        
        # Keep only last 20 favorites
        favorites = favorites[:20]
        
        return CookieManager.set_cookie(response, CookieManager.FAVORITE_ROUTES, favorites)
    
    @staticmethod
    def get_favorite_routes(request):
        """
        Get favorite routes from cookies
        """
        return CookieManager.get_cookie(request, CookieManager.FAVORITE_ROUTES, [])
    
    @staticmethod
    def set_booking_preferences(response, preferences):
        """
        Store booking-specific preferences
        preferences = {
            'auto_confirm': True,
            'share_location': True,
            'sms_updates': True,
            'email_notifications': False
        }
        """
        return CookieManager.set_cookie(response, CookieManager.BOOKING_PREFERENCES, preferences)
    
    @staticmethod
    def get_booking_preferences(request):
        """
        Get booking preferences from cookies
        """
        return CookieManager.get_cookie(request, CookieManager.BOOKING_PREFERENCES, {
            'auto_confirm': True,
            'share_location': True,
            'sms_updates': True,
            'email_notifications': False
        })


def cookie_middleware(get_response):
    """
    Middleware to handle cookie operations
    """
    def middleware(request):
        # Add cookie manager to request
        request.cookie_manager = CookieManager()
        
        response = get_response(request)
        
        # You can add global cookie operations here if needed
        return response
    
    return middleware