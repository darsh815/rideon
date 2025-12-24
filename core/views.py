from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.documentation import generate_documentation_file
from core.models import Driver, Wallet, WalletTransaction, Booking
from core.cookie_utils import CookieManager
import json
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import csv
import os

# --- Download Receipt View ---
@login_required
def download_receipt(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user, status='Paid')
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found or not paid')
        return redirect('booking_history')
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica", 16)
    p.drawString(100, 800, "RideON Receipt")
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Booking ID: {booking.pk}")
    p.drawString(100, 730, f"Vehicle: {booking.vehicle_type}")
    p.drawString(100, 710, f"Price: ₹{booking.price}")
    p.drawString(100, 690, f"From: {booking.pickup}")
    p.drawString(100, 670, f"To: {booking.destination}")
    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{booking.pk}.pdf"'
    return response

# AJAX endpoint for promocode application

# AJAX endpoint for promocode application
@csrf_exempt
def apply_promocode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            vehicle_type = data.get('vehicle_type')
            price = data.get('price')
            promocode = data.get('promocode', '').strip().lower()
            already_discounted = data.get('already_discounted', False)
        except Exception:
            return JsonResponse({'valid': False, 'error': 'Invalid request'}, status=400)
        promocodes = {
            'freefirst': 100,
            'save50': 50,
            'ride10': 10,
            'car20': 20,
        }
        try:
            price_decimal = Decimal(str(price))
        except Exception:
            return JsonResponse({'valid': False, 'error': 'Invalid price'}, status=400)
        if already_discounted:
            price_int = int(price_decimal.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            return JsonResponse({'valid': False, 'price': price_int, 'discount': 0})
        if promocode == 'freeride':
            max_discount = Decimal('50')
            discount_amount = min(price_decimal, max_discount)
            discounted_price = (price_decimal - discount_amount).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return JsonResponse({'valid': True, 'price': int(discounted_price), 'discount': int(discount_amount)})
        discount_percent = promocodes.get(promocode, 0)
        if discount_percent > 0:
            discounted_price = price_decimal * (Decimal('1') - Decimal(discount_percent) / Decimal('100'))
            discounted_price = discounted_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return JsonResponse({'valid': True, 'price': int(discounted_price), 'discount': int(discount_percent)})
        price_int = int(price_decimal.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        return JsonResponse({'valid': False, 'price': price_int, 'discount': 0})

@login_required
def admin_dashboard_view(request):
    from accounts.models import UserProfile
    is_admin = False
    profile = UserProfile.objects.filter(user=request.user).first()
    if profile and profile.is_admin:
        is_admin = True
    elif request.user.is_staff or request.user.is_superuser:
        is_admin = True
    if not is_admin:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    ongoing_bookings = Booking.objects.filter(
        status__in=['Driver Assigned', 'In Progress']
    ).select_related('user', 'driver').order_by('-created_at')
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        try:
            booking = Booking.objects.get(id=booking_id)
            if action == 'start_trip':
                booking.status = 'In Progress'
                booking.save()
                messages.success(request, f'Trip started for {booking.user.username}')
            elif action == 'end_trip':
                booking.status = 'Completed'
                booking.save()
                messages.success(request, f'Trip completed for {booking.user.username}')
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found')
        return redirect('admin_dashboard')
    context = {
        'ongoing_bookings': ongoing_bookings,
        'total_ongoing': ongoing_bookings.count(),
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def trip_payment_view(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user, status='Completed')
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found or not completed')
        return redirect('booking_history')
    if booking.status == 'Paid':
        messages.info(request, 'This booking has already been paid')
        return redirect('booking_history')
    if booking.price <= 0:
        messages.error(request, 'Invalid booking price')
        return redirect('booking_history')
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': Decimal('0.00')}
    )
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if not payment_method:
            messages.error(request, 'Please select a payment method')
        elif payment_method == 'wallet':
            if wallet.balance < booking.price:
                messages.error(request, f'Insufficient wallet balance. You need ₹{booking.price} but have ₹{wallet.balance}')
            else:
                try:
                    wallet.refresh_from_db()
                    if wallet.balance < booking.price:
                        messages.error(request, 'Insufficient wallet balance after verification')
                    else:
                        wallet.balance -= booking.price
                        wallet.save()
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            amount=-booking.price,
                            transaction_type='debit',
                            description=f'Trip payment for booking #{booking.pk}'
                        )
                        booking.status = 'Paid'
                        booking.save()
                        messages.success(request, f'Payment of ₹{booking.price} successful! You can now book another ride.')
                        return redirect('booking_history')
                except Exception:
                    messages.error(request, 'Payment processing failed. Please try again.')
        elif payment_method == 'cash':
            try:
                booking.status = 'Paid'
                booking.save()
                messages.success(request, 'Cash payment confirmed! You can now book another ride.')
                return redirect('booking_history')
            except Exception:
                messages.error(request, 'Error confirming cash payment. Please try again.')
        else:
            messages.error(request, 'Invalid payment method selected')
    context = {
        'booking': booking,
        'wallet': wallet,
        'wallet_balance': wallet.balance if wallet else 0,
    }
    return render(request, 'core/trip_payment.html', context)

@login_required
def booking_history_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    active_statuses = ['Pending', 'Confirmed', 'Driver Assigned', 'In Progress', 'Completed']
    has_active_trip = Booking.objects.filter(
        user=request.user, 
        status__in=active_statuses
    ).exclude(status='Paid').exists()
    return render(request, 'core/booking_history.html', {
        'bookings': bookings,
        'has_active_trip': has_active_trip,
    })

@login_required
def download_bookings_csv_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=\"bookings.csv\"'
    writer = csv.writer(response)
    writer.writerow(['Booking ID', 'Vehicle', 'Price', 'Pickup', 'Destination', 'Status', 'Created At'])
    for b in bookings:
        writer.writerow([b.pk, b.vehicle_type, str(b.price), b.pickup, b.destination, b.status, b.created_at])
    return response

@login_required
def cancel_booking_view(request):
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        booking = Booking.objects.filter(id=booking_id, user=request.user, can_cancel=True, status='Confirmed').first()
        if booking:
            booking.status = 'Cancelled'
            booking.can_cancel = False
            booking.save()
    return redirect('booking_history')

@login_required
def submit_feedback_view(request):
    if request.method == 'POST':
        return redirect('booking_history')
    return redirect('booking_history')

@login_required
def add_wallet_balance_view(request):
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': Decimal('0.00')}
    )
    amount = request.POST.get('amount')
    try:
        if amount:
            amount_decimal = Decimal(str(amount))
            if amount_decimal > 0:
                wallet.balance += amount_decimal
                wallet.save()
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount_decimal,
                    transaction_type='credit',
                    description=f'Wallet top-up of ₹{amount_decimal}'
                )
                messages.success(request, f'₹{amount_decimal} added to your wallet successfully!')
            else:
                messages.error(request, 'Amount must be greater than 0')
        else:
            messages.error(request, 'Please enter a valid amount')
    except Exception:
        messages.error(request, 'Error processing wallet top-up. Please try again.')
    return render(request, 'core/add_wallet_balance.html', {'wallet': wallet})

def contact_view(request):
    return render(request, 'core/contact.html')

def about_view(request):
    return render(request, 'core/about.html')

def home_view(request):
    vehicles = []
    pickup = request.GET.get('pickup', '')
    destination = request.GET.get('destination', '')
    promocode = request.GET.get('promocode', '').strip().lower()
    discount = 0
    if request.method == 'POST' and 'rent_vehicle_type' in request.POST:
        vehicle_type = request.POST.get('rent_vehicle_type')
        price = request.POST.get('rent_price')
        payment_method = request.POST.get('payment_method')
        Booking.objects.create(
            user=request.user,
            vehicle_type=vehicle_type,
            price=price,
            pickup='Rental',
            destination='Rental',
            status='Rented',
        )
        return render(request, 'core/booking_success.html', {
            'vehicle_type': vehicle_type,
            'price': price,
            'pickup': 'Rental',
            'destination': 'Rental',
            'payment_method': payment_method,
            'promocode': '',
            'discount': 0,
        })
    if request.method == 'POST' and 'vehicle_type' not in request.POST:
        pickup = request.POST.get('pickup')
        destination = request.POST.get('destination')
        promocode = request.POST.get('promocode', '').strip().lower()
    promocodes = {
        'freefirst': 100,
        'save50': 50,
        'ride10': 10,
        'car20': 20,
    }
    discount = 0
    if promocode in promocodes:
        discount = promocodes[promocode]
    if pickup and destination:
        import requests
        import time
        def get_coords_advanced(place):
            try:
                url = f'https://nominatim.openstreetmap.org/search?format=json&q={place}&limit=1'
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'RideON-App/1.0'})
                data = resp.json()
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])
            except Exception:
                pass
            city_coords = {
                'mumbai': (19.0760, 72.8777),
                'delhi': (28.7041, 77.1025),
                'bangalore': (12.9716, 77.5946),
                'chennai': (13.0827, 80.2707),
                'kolkata': (22.5726, 88.3639),
                'hyderabad': (17.3850, 78.4867),
                'pune': (18.5204, 73.8567),
                'airport': (19.0896, 72.8656),
                'station': (19.0330, 72.8347),
            }
            place_lower = place.lower()
            for city, coords in city_coords.items():
                if city in place_lower:
                    return coords
            return None, None
        def haversine_advanced(lat1, lon1, lat2, lon2):
            from math import radians, sin, cos, sqrt, atan2, asin
            try:
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                R = 6371.0
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                distance = R * c
                if distance < 0.1:
                    return 0.5
                elif distance > 2000:
                    return 50.0
                elif not (distance == distance):
                    return 10.0
                return round(distance, 2)
            except Exception:
                return 10.0
        lat1, lon1 = get_coords_advanced(pickup)
        lat2, lon2 = get_coords_advanced(destination)
        if lat1 is None or lat2 is None:
            dist = 15.0
        else:
            dist = haversine_advanced(lat1, lon1, lat2, lon2)
        vehicle_types = [
            {'type': 'Scooter', 'base': 15, 'per_km': 5},
            {'type': 'Saver Scooter', 'base': 12, 'per_km': 4},
            {'type': 'Bike', 'base': 20, 'per_km': 6},
            {'type': 'Rickshaw', 'base': 25, 'per_km': 8},
            {'type': 'Mini', 'base': 50, 'per_km': 12},
            {'type': 'SUV', 'base': 120, 'per_km': 20},
            {'type': 'Auto', 'base': 30, 'per_km': 9},
        ]
        filtered = []
        for v in vehicle_types:
            if dist < 5:
                filtered.append(v)
            elif 5 <= dist < 25:
                if v['type'] != 'SUV' or dist >= 15:
                    filtered.append(v)
            elif 25 <= dist < 100:
                filtered.append(v)
            elif dist >= 100:
                if v['type'] not in ['Scooter', 'Saver Scooter']:
                    filtered.append(v)
            else:
                filtered.append(v)
        vehicles = []
        def calculate_advanced_fare(vehicle_data, distance, discount=0):
            base_fare = Decimal(str(vehicle_data['base']))
            per_km_rate = Decimal(str(vehicle_data['per_km']))
            distance_decimal = Decimal(str(distance))
            distance_charge = per_km_rate * distance_decimal
            if distance <= 2:
                fare = max(base_fare * Decimal('1.5'), base_fare + distance_charge)
            elif distance <= 5:
                fare = base_fare + distance_charge
            elif distance <= 15:
                fare = base_fare + (distance_charge * Decimal('0.95'))
            elif distance <= 50:
                base_distance = Decimal('15')
                excess_distance = distance_decimal - base_distance
                fare = base_fare + (per_km_rate * base_distance * Decimal('0.95')) + (per_km_rate * excess_distance * Decimal('0.85'))
            else:
                base_distance = Decimal('15')
                medium_distance = Decimal('35')
                excess_distance = distance_decimal - Decimal('50')
                fare = (base_fare +
                        (per_km_rate * base_distance * Decimal('0.95')) +
                        (per_km_rate * medium_distance * Decimal('0.85')) +
                        (per_km_rate * excess_distance * Decimal('0.75')))
            from datetime import datetime
            current_hour = datetime.now().hour
            if 7 <= current_hour <= 10 or 17 <= current_hour <= 20:
                fare = fare * Decimal('1.15')
            elif 22 <= current_hour or current_hour <= 5:
                fare = fare * Decimal('1.10')
            if vehicle_data['type'] in ['SUV', 'Mini']:
                fare = fare * Decimal('1.05')
            elif vehicle_data['type'] in ['Saver Scooter']:
                fare = fare * Decimal('0.95')
            if discount:
                fare = fare * (Decimal('1') - Decimal(discount)/Decimal('100'))
            fare = fare.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return max(1, min(int(fare), 99999))
        for v in filtered:
            price = calculate_advanced_fare(v, dist, discount)
            vehicles.append({
                'type': v['type'],
                'price': price,
                'base_fare': v['base'],
                'per_km_rate': v['per_km'],
                'distance': round(dist, 1),
                'fare_breakdown': {
                    'base': v['base'],
                    'distance_charge': round((price - v['base']) * 0.8, 1),
                    'surcharges': round((price - v['base']) * 0.2, 1)
                }
            })
    else:
        vehicle_types = [
            {'type': 'Scooter', 'base': 15, 'per_km': 5},
            {'type': 'Saver Scooter', 'base': 12, 'per_km': 4},
            {'type': 'Bike', 'base': 20, 'per_km': 6},
            {'type': 'Rickshaw', 'base': 25, 'per_km': 8},
            {'type': 'Mini', 'base': 50, 'per_km': 12},
            {'type': 'SUV', 'base': 120, 'per_km': 20},
            {'type': 'Auto', 'base': 30, 'per_km': 9},
        ]
        def calculate_default_fare(vehicle_data, discount=0):
            default_distance = 10.0
            base_fare = Decimal(str(vehicle_data['base']))
            per_km_rate = Decimal(str(vehicle_data['per_km']))
            fare = base_fare + (per_km_rate * Decimal(str(default_distance)) * Decimal('0.95'))
            from datetime import datetime
            current_hour = datetime.now().hour
            if 7 <= current_hour <= 10 or 17 <= current_hour <= 20:
                fare = fare * Decimal('1.15')
            elif 22 <= current_hour or current_hour <= 5:
                fare = fare * Decimal('1.10')
            if vehicle_data['type'] in ['SUV', 'Mini']:
                fare = fare * Decimal('1.05')
            elif vehicle_data['type'] in ['Saver Scooter']:
                fare = fare * Decimal('0.95')
            if discount:
                fare = fare * (Decimal('1') - Decimal(discount)/Decimal('100'))
            fare = fare.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return max(1, min(int(fare), 99999))
        vehicles = []
        for v in vehicle_types:
            price = calculate_default_fare(v, discount)
            vehicles.append({
                'type': v['type'],
                'price': price,
                'base_fare': v['base'],
                'per_km_rate': v['per_km'],
                'distance': 10.0,
                'fare_breakdown': {
                    'base': v['base'],
                    'distance_charge': round((price - v['base']) * 0.8, 1),
                    'surcharges': round((price - v['base']) * 0.2, 1)
                }
            })
    return render(request, 'core/home.html', {
        'vehicles': vehicles,
        'pickup': pickup,
        'destination': destination,
        'promocode': promocode,
        'discount': discount,
    })

@login_required
def book_vehicle_view(request):
    user = request.user
    wallet = Wallet.objects.filter(user=user).first()
    active_statuses = ['Pending', 'Confirmed', 'Driver Assigned', 'In Progress', 'Completed']
    active_booking = Booking.objects.filter(
        user=user, 
        status__in=active_statuses
    ).exclude(status='Paid').first()
    if active_booking:
        if request.method == 'POST':
            messages.error(request, 'You already have an active trip. Please complete your current trip before booking another one.')
            return redirect('booking_history')
        return render(request, 'core/booking.html', {
            'active_booking': active_booking,
            'wallet': wallet,
            'has_active_trip': True,
        })
    if request.method == 'POST':
        vehicle_type = request.POST.get('vehicle_type')
        price = request.POST.get('price')
        pickup = request.POST.get('pickup')
        destination = request.POST.get('destination')
        payment_method = request.POST.get('payment_method')
        promocode = request.POST.get('promocode', '').strip().lower()
        promocodes = {
            'freefirst': 100,
            'save50': 50,
            'ride10': 10,
            'car20': 20,
        }
        discount = 0
        if promocode in promocodes:
            discount = promocodes[promocode]
        try:
            price_decimal = Decimal(price)
        except (InvalidOperation, TypeError):
            price_decimal = Decimal('0')
        if discount > 0 and price_decimal > 0:
            price_decimal = price_decimal * (Decimal('1') - Decimal(discount)/Decimal('100'))
            price_decimal = price_decimal.quantize(Decimal('1'))
        available_driver = Driver.objects.filter(vehicle_type__icontains=vehicle_type).first()
        if not available_driver:
            available_driver = Driver.objects.create(
                name=f"Driver {vehicle_type}",
                phone="+91-9876543210",
                vehicle_type=vehicle_type,
                vehicle_number=f"{vehicle_type.upper()[:2]}-{user.id:04d}",
                rating=4.5
            )
        booking = Booking.objects.create(
            user=user,
            vehicle_type=vehicle_type,
            price=price_decimal,
            pickup=pickup,
            destination=destination,
            status='Driver Assigned',
            driver=available_driver,
            vehicle_number=available_driver.vehicle_number if available_driver else None,
        )
        response = render(request, 'core/booking_success.html', {
            'booking': booking,
            'vehicle_type': vehicle_type,
            'price': str(price_decimal),
            'pickup': pickup,
            'destination': destination,
            'payment_method': payment_method,
            'promocode': promocode,
            'discount': discount,
            'driver': available_driver,
            'payment_success': False,
            'payment_pending': True,
        })
        CookieManager.set_last_vehicle_type(response, vehicle_type)
        CookieManager.add_recent_location(response, request, 'pickup', pickup)
        CookieManager.add_recent_location(response, request, 'destination', destination)
        booking_prefs = CookieManager.get_booking_preferences(request)
        if booking_prefs is None:
            booking_prefs = {}
        booking_prefs['last_payment_method'] = payment_method
        CookieManager.set_booking_preferences(response, booking_prefs)
        return response
    vehicle_type = request.GET.get('vehicle_type')
    price = request.GET.get('price')
    pickup = request.GET.get('pickup')
    destination = request.GET.get('destination')
    user_prefs = CookieManager.get_user_preferences(request)
    recent_locations = CookieManager.get_recent_locations(request)
    last_vehicle_type = CookieManager.get_last_vehicle_type(request)
    booking_prefs = CookieManager.get_booking_preferences(request)
    if not vehicle_type:
        vehicle_type = user_prefs.get('preferred_vehicle', last_vehicle_type) if user_prefs else last_vehicle_type
    return render(request, 'core/booking.html', {
        'vehicle_type': vehicle_type,
        'price': price,
        'pickup': pickup,
        'destination': destination,
        'wallet': wallet,
        'recent_locations': recent_locations,
        'user_preferences': user_prefs,
        'booking_preferences': booking_prefs,
        'last_vehicle_type': last_vehicle_type,
    })

@login_required
def trip_details_view(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        if booking.status not in ['Driver Assigned', 'In Progress']:
            messages.error(request, 'Trip details only available for active trips.')
            return redirect('booking_history')
        return render(request, 'core/trip_details.html', {'booking': booking})
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('booking_history')

@csrf_exempt
@login_required
def complete_trip_view(request, booking_id):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
            booking.status = 'Completed'
            booking.save()
            return JsonResponse({'success': True, 'message': 'Trip completed successfully'})
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@login_required
def user_preferences_view(request):
    if request.method == 'POST':
        preferences = {
            'preferred_vehicle': request.POST.get('preferred_vehicle', 'Auto'),
            'preferred_payment': request.POST.get('preferred_payment', 'wallet'),
            'theme': request.POST.get('theme', 'light'),
            'notifications': request.POST.get('notifications') == 'on'
        }
        booking_preferences = {
            'auto_confirm': request.POST.get('auto_confirm') == 'on',
            'share_location': request.POST.get('share_location') == 'on',
            'sms_updates': request.POST.get('sms_updates') == 'on',
            # 'email_notifications': request.POST.get('email_notifications') == 'on'  # Email notifications removed
        }
        response = redirect('user_preferences')
        CookieManager.set_user_preferences(response, preferences)
        CookieManager.set_booking_preferences(response, booking_preferences)
        messages.success(request, 'Preferences saved successfully!')
        return response
    user_prefs = CookieManager.get_user_preferences(request)
    booking_prefs = CookieManager.get_booking_preferences(request)
    recent_locations = CookieManager.get_recent_locations(request)
    favorite_routes = CookieManager.get_favorite_routes(request)
    return render(request, 'core/user_preferences.html', {
        'user_preferences': user_prefs,
        'booking_preferences': booking_prefs,
        'recent_locations': recent_locations,
        'favorite_routes': favorite_routes,
    })

@csrf_exempt
@login_required
def clear_preferences_view(request):
    if request.method == 'POST':
        response = JsonResponse({'success': True, 'message': 'Preferences cleared'})
        CookieManager.delete_cookie(response, CookieManager.USER_PREFERENCES)
        CookieManager.delete_cookie(response, CookieManager.RECENT_LOCATIONS)
        CookieManager.delete_cookie(response, CookieManager.FAVORITE_ROUTES)
        CookieManager.delete_cookie(response, CookieManager.BOOKING_PREFERENCES)
        CookieManager.delete_cookie(response, CookieManager.LAST_VEHICLE_TYPE)
        return response
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@login_required
def documentation_view(request):
    context = {
        'page_title': 'Project Documentation',
        'documentation_available': True,
    }
    return render(request, 'core/documentation.html', context)

@login_required 
def download_documentation(request):
    try:
        buffer, error = generate_documentation_file()
        if error or buffer is None:
            messages.error(request, f"Error generating documentation: {error or 'Unknown error'}")
            return redirect('documentation')
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = 'attachment; filename=\"RideON_Complete_Documentation.docx\"'
        response['Content-Length'] = len(buffer.getvalue())
        return response
    except Exception as e:
        messages.error(request, f"Error generating documentation: {str(e)}")
        return redirect('documentation')
