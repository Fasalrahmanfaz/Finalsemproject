from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe
from .models import Booking
from enquiries.models import Enquiry


@login_required
def my_bookings(request):
    if request.user.role != 'customer':
        return redirect('core:home')
    bookings = request.user.bookings.select_related('band', 'package').order_by('-event_date')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    # Allow customer or band manager to cancel
    if booking.customer != request.user and booking.band.manager != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if booking.status == 'confirmed':
        booking.status = 'cancelled'
        booking.save()
        booking.enquiry.status = 'cancelled'
        booking.enquiry.save()

        # Free up the date
        from bands.models import BandAvailability
        BandAvailability.objects.filter(band=booking.band, date=booking.event_date).update(status='available')

        # Notify the other party
        if request.user == booking.customer:
            recipient = booking.band.email
            notify_name = booking.band.band_name
        else:
            recipient = booking.customer.email
            notify_name = booking.customer.get_full_name()

        send_mail(
            subject=f'Booking Cancelled - {booking.enquiry.reference_number}',
            message=f'The booking for {booking.event_date} has been cancelled by {request.user.get_full_name()}. Reference: {booking.enquiry.reference_number}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=True,
        )
        messages.success(request, 'Booking cancelled successfully.')
    else:
        messages.error(request, f'Cannot cancel a {booking.status} booking.')

    if request.user.role == 'band_manager':
        return redirect('bookings:manager_bookings')
    return redirect('bookings:my_bookings')


@login_required
def manager_bookings(request):
    """Band Manager: view all bookings"""
    if request.user.role != 'band_manager':
        return redirect('core:home')
    try:
        band = request.user.band_profile
    except Exception:
        messages.error(request, 'Create a band profile first.')
        return redirect('bands:create_profile')

    bookings = band.bookings.select_related('customer', 'package').order_by('-event_date')
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    return render(request, 'bookings/manager_bookings.html', {'bookings': bookings, 'status_filter': status_filter, 'band': band})


@login_required
def mark_completed(request, pk):
    """Band Manager marks event as completed → triggers rating email"""
    if request.user.role != 'band_manager':
        return redirect('core:home')
    booking = get_object_or_404(Booking, pk=pk, band__manager=request.user)
    if booking.status == 'confirmed':
        booking.status = 'completed'
        booking.save()
        booking.enquiry.status = 'completed'
        booking.enquiry.save()

        # Increment events attended
        booking.band.events_attended += 1
        booking.band.save()

        # Send rating prompt to customer
        if not booking.rating_prompt_sent:
            rating_url = f'/reviews/rate/{booking.pk}/'
            send_mail(
                subject=f'How was {booking.band.band_name}? Rate your experience!',
                message=f'''Hi {booking.customer.first_name},

We hope your event was amazing! 

Please take a moment to rate {booking.band.band_name}:
{rating_url}

Your feedback helps other customers make informed decisions.

Thank you for choosing Bandez!
— The Bandez Team''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.customer.email],
                fail_silently=True,
            )
            booking.rating_prompt_sent = True
            booking.save()

        messages.success(request, f'Event marked as completed! Events count updated to {booking.band.events_attended}.')
    else:
        messages.error(request, 'Only confirmed bookings can be marked as completed.')
    return redirect('bookings:manager_bookings')


@login_required
def mark_fully_paid(request, pk):
    """Band Manager marks an advance/offline booking as fully paid"""
    if request.user.role != 'band_manager':
        return redirect('core:home')
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk, band__manager=request.user)
        if booking.status == 'confirmed' and booking.payment_status != 'paid':
            booking.payment_status = 'paid'
            booking.save()
            messages.success(request, f'Booking for {booking.customer.first_name} marked as fully paid!')
        else:
            messages.error(request, 'Cannot update payment status for this booking.')
    return redirect('bookings:manager_bookings')


@login_required
def create_checkout_session(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user, status='pending_payment')
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    domain_url = request.build_absolute_uri('/')[:-1]  # Get base domain
    
    amount_to_charge = booking.agreed_amount
    if booking.payment_type == 'advance' and booking.advance_amount:
        amount_to_charge = booking.advance_amount
        
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'inr',
                        'unit_amount': amount_to_charge * 100,  # Stripe expects amount in paise (smallest currency unit)
                        'product_data': {
                            'name': f"Booking with {booking.band.band_name}",
                            'description': f"{'Advance Payment for ' if booking.payment_type == 'advance' else 'Full Payment for '}Event: {booking.enquiry.get_event_type_display()} on {booking.event_date}",
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'booking_id': booking.id,
            },
            mode='payment',
            success_url=domain_url + reverse('bookings:payment_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + reverse('bookings:payment_cancel'),
        )
        
        booking.stripe_checkout_session_id = checkout_session.id
        booking.save()
        
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        messages.error(request, f"Error creating payment session: {str(e)}")
        return redirect('bookings:my_bookings')


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            booking_id = session.metadata.get('booking_id')
            booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
            
            # Note: Webhook is safer, but we can also update status securely here if paid
            if session.payment_status == 'paid' and booking.status == 'pending_payment':
                booking.status = 'confirmed'
                booking.payment_status = 'paid'
                booking.save()
                messages.success(request, 'Payment successful! Your booking is now confirmed.')
        except Exception:
            pass
            
    return render(request, 'bookings/payment_success.html')


@login_required
def payment_cancel(request):
    messages.info(request, 'Payment was cancelled. You can try again later.')
    return redirect('bookings:my_bookings')


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.status = 'confirmed'
                booking.payment_status = 'paid'
                booking.save()
                
                # Notify manager and customer
                send_mail(
                    subject=f'Payment Received & Booking Confirmed! - {booking.enquiry.reference_number}',
                    message=f'The customer has successfully paid for the booking on {booking.event_date}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking.band.email, booking.customer.email],
                    fail_silently=True,
                )
            except Booking.DoesNotExist:
                pass

    return HttpResponse(status=200)
