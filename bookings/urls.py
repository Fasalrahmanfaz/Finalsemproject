from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('<int:pk>/', views.booking_detail, name='booking_detail'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('manage/', views.manager_bookings, name='manager_bookings'),
    path('manage/<int:pk>/complete/', views.mark_completed, name='mark_completed'),
    path('manage/<int:pk>/paid/', views.mark_fully_paid, name='mark_fully_paid'),
    
    # Payments
    path('<int:pk>/checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
