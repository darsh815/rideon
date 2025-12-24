from django.urls import path
from . import views
from . import views_payment

urlpatterns = [
    path('', views.home_view, name='home'),
    path('booking/', views.book_vehicle_view, name='booking'),
    path('book/', views.book_vehicle_view, name='book_vehicle'),
    path('booking_history/', views.booking_history_view, name='booking_history'),
    path('add_wallet_balance/', views.add_wallet_balance_view, name='add_wallet_balance'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('trip_payment/<int:booking_id>/', views.trip_payment_view, name='trip_payment'),
    path('trip_details/<int:booking_id>/', views.trip_details_view, name='trip_details'),
    path('complete_trip/<int:booking_id>/', views.complete_trip_view, name='complete_trip'),
    path('download_bookings_csv/', views.download_bookings_csv_view, name='download_bookings_csv'),
    path('preferences/', views.user_preferences_view, name='user_preferences'),
    path('clear_preferences/', views.clear_preferences_view, name='clear_preferences'),
    path('cancel_booking/', views.cancel_booking_view, name='cancel_booking'),
    path('submit_feedback/', views.submit_feedback_view, name='submit_feedback'),
    path('pay/<int:booking_id>/', views_payment.payment_page, name='payment_page'),
    path('payment_success/', views_payment.payment_success, name='payment_success'),
    path('apply_promocode/', views.apply_promocode, name='apply_promocode'),
    path('documentation/', views.documentation_view, name='documentation'),
    path('download_documentation/', views.download_documentation, name='download_documentation'),
    path('download_receipt/<int:booking_id>/', views.download_receipt, name='download_receipt'),
]
