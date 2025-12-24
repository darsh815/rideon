
import json

from django.http import HttpResponse



class CookieManager:

    """Utility class for managing user preference cookies"""

    

    # Cookie names

    USER_PREFERENCES = 'user_preferences'

    RECENT_LOCATIONS = 'recent_locations'

    FAVORITE_ROUTES = 'favorite_routes'

    BOOKING_PREFERENCES = 'booking_preferences'

    LAST_VEHICLE_TYPE = 'last_vehicle_type'

    

    @staticmethod

    def set_user_preferences(response, preferences):

        """Store user preferences in cookie"""

        response.set_cookie(

            CookieManager.USER_PREFERENCES,

            json.dumps(preferences),

            max_age=30*24*60*60,  # 30 days

            httponly=True,

            samesite='Lax'

        )

    

    @staticmethod

    def get_user_preferences(request):

        """Retrieve user preferences from cookie"""

        prefs = request.COOKIES.get(CookieManager.USER_PREFERENCES)

        return json.loads(prefs) if prefs else None

    

    @staticmethod

    def set_booking_preferences(response, preferences):

        """Store booking preferences in cookie"""

        response.set_cookie(

            CookieManager.BOOKING_PREFERENCES,

            json.dumps(preferences),

            max_age=30*24*60*60,

            httponly=True,

            samesite='Lax'

        )

    

    @staticmethod

    def get_booking_preferences(request):

        """Retrieve booking preferences from cookie"""

        prefs = request.COOKIES.get(CookieManager.BOOKING_PREFERENCES)

        return json.loads(prefs) if prefs else None

    

    @staticmethod

    def set_last_vehicle_type(response, vehicle_type):

        """Store last selected vehicle type"""

        response.set_cookie(

            CookieManager.LAST_VEHICLE_TYPE,

            vehicle_type,

            max_age=90*24*60*60,  # 90 days

            httponly=True,

            samesite='Lax'

        )

    

    @staticmethod

    def get_last_vehicle_type(request):

        """Retrieve last selected vehicle type"""

        return request.COOKIES.get(CookieManager.LAST_VEHICLE_TYPE)

    

    @staticmethod

    def add_recent_location(response, request, location_type, location):

        """Add a location to recent locations list"""

        recent = request.COOKIES.get(CookieManager.RECENT_LOCATIONS)

        recent_list = json.loads(recent) if recent else {'pickups': [], 'destinations': []}

        

        key = 'pickups' if location_type == 'pickup' else 'destinations'

        if location not in recent_list[key]:

            recent_list[key].insert(0, location)

            recent_list[key] = recent_list[key][:10]  # Keep last 10

        

        response.set_cookie(

            CookieManager.RECENT_LOCATIONS,

            json.dumps(recent_list),

            max_age=90*24*60*60,

            httponly=True,

            samesite='Lax'

        )

    

    @staticmethod

    def get_recent_locations(request):

        """Retrieve recent locations"""

        locations = request.COOKIES.get(CookieManager.RECENT_LOCATIONS)

        return json.loads(locations) if locations else {'pickups': [], 'destinations': []}

    

    @staticmethod

    def get_favorite_routes(request):

        """Retrieve favorite routes"""

        routes = request.COOKIES.get(CookieManager.FAVORITE_ROUTES)

        return json.loads(routes) if routes else []

    

    @staticmethod

    def delete_cookie(response, cookie_name):

        """Delete a cookie"""

        response.delete_cookie(cookie_name)

