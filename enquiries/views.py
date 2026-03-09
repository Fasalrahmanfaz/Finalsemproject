from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Enquiry, EnquiryMessage
from .forms import EnquiryForm
from bands.models import BandProfile
from core.ai_engine import classify_enquiry, get_auto_response




@login_required
def submit_enquiry(request, band_id):
    if request.user.role != 'customer':
        messages.error(request, 'Only customers can submit enquiries.')
        return redirect('bands:explore')

    band = get_object_or_404(BandProfile, pk=band_id, is_active=True)

    alternative_bands = []
    date_unavailable = False

    if request.method == 'POST':
        form = EnquiryForm(band=band, data=request.POST)
        if form.is_valid():
            event_date = form.cleaned_data['event_date']

            # Check if band is available on this date
            from bands.models import BandAvailability
            from bookings.models import Booking
            from bands.views import get_recommendations

            avail = BandAvailability.objects.filter(band=band, date=event_date).first()
            has_booking = Booking.objects.filter(band=band, event_date=event_date, status='confirmed').exists()

            if has_booking or (avail and avail.status in ['booked', 'blocked']):
                date_unavailable = True
                messages.error(request, f'{band.band_name} is not available on {event_date}. Please choose another date or try a similar band below.')

                # Find alternative bands available on this date
                similar = get_recommendations(
                    event_types=band.event_types,
                    location=band.base_location,
                    exclude_ids=[band.id],
                    limit=10
                )
                for alt_band in similar:
                    alt_avail = BandAvailability.objects.filter(band=alt_band, date=event_date).first()
                    alt_booked = Booking.objects.filter(band=alt_band, event_date=event_date, status='confirmed').exists()
                    if not alt_booked and (not alt_avail or alt_avail.status == 'available'):
                        alternative_bands.append(alt_band)
                    if len(alternative_bands) >= 4:
                        break
            else:
                enquiry = form.save(commit=False)
                enquiry.customer = request.user
                enquiry.band = band

                # AI Classification
                category, confidence = classify_enquiry(enquiry.message)
                enquiry.ai_category = category
                enquiry.ai_confidence = confidence
                enquiry.save()

                # Send auto-reply to customer
                auto_response = get_auto_response(category, enquiry)
                send_mail(
                    subject=f'Enquiry Received - {band.band_name} [Ref: {enquiry.reference_number}]',
                    message=f'Dear {request.user.first_name},\n\n{auto_response}\n\nTrack your enquiry at: /enquiries/my-enquiries/',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )

                # Notify band manager
                send_mail(
                    subject=f'New Enquiry - {enquiry.reference_number} ({enquiry.get_event_type_display()})',
                    message=f'''New enquiry received!

Reference: {enquiry.reference_number}
Customer: {request.user.get_full_name()} ({request.user.email})
Event Type: {enquiry.get_event_type_display()}
Event Date: {enquiry.event_date}
Location: {enquiry.event_location}
Duration: {enquiry.performance_duration} hours
Audience: {enquiry.expected_audience}

AI Category: {enquiry.get_ai_category_display()}

Message:
{enquiry.message}

Log in to manage this enquiry.''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[band.email],
                    fail_silently=True,
                )

                enquiry.auto_reply_sent = True
                enquiry.save()
                messages.success(request, f'Enquiry submitted! Reference: {enquiry.reference_number}')
                return redirect('enquiries:enquiry_success', pk=enquiry.pk)
    else:
        form = EnquiryForm(band=band)

    # Pricing data for the estimator
    packages = band.packages.filter(is_active=True)
    context = {
        'form': form,
        'band': band,
        'packages': packages,
        'packages_json': _packages_json(packages),
        'alternative_bands': alternative_bands,
        'date_unavailable': date_unavailable,
    }
    return render(request, 'enquiries/submit_enquiry.html', context)


def _packages_json(packages):
    import json
    return json.dumps([{
        'id': p.id, 'name': p.name, 'min': p.min_price, 'max': p.max_price, 'hours': p.duration_hours
    } for p in packages])


@login_required
def enquiry_success(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk, customer=request.user)
    # Band recommendations
    from bands.views import get_recommendations
    similar = get_recommendations(event_types=enquiry.band.event_types, exclude_ids=[enquiry.band.id])[:3]
    return render(request, 'enquiries/success.html', {'enquiry': enquiry, 'similar_bands': similar})


@login_required
def my_enquiries(request):
    """Customer: view all their enquiries"""
    if request.user.role != 'customer':
        return redirect('core:home')
    enquiries = request.user.enquiries.select_related('band').order_by('-created_at')
    return render(request, 'enquiries/my_enquiries.html', {'enquiries': enquiries})


@login_required
def enquiry_detail(request, pk):
    """Customer or Band Manager: view single enquiry detail with chat"""
    enquiry = get_object_or_404(Enquiry, pk=pk)
    # Allow access to the customer who submitted OR the band manager who received it
    if request.user == enquiry.customer:
        pass  # customer can view their own enquiry
    elif request.user.role == 'band_manager' and hasattr(request.user, 'band_profile') and enquiry.band == request.user.band_profile:
        pass  # band manager can view enquiries sent to their band
    else:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to view this enquiry.")
    chat_messages = enquiry.messages.select_related('sender').order_by('created_at')
    return render(request, 'enquiries/enquiry_detail.html', {
        'enquiry': enquiry,
        'chat_messages': chat_messages,
    })


@login_required
def send_enquiry_message(request, pk):
    """Send a chat message on an enquiry"""
    enquiry = get_object_or_404(Enquiry, pk=pk)
    # Permission check: only customer or band manager
    is_customer = request.user == enquiry.customer
    is_manager = (
        request.user.role == 'band_manager'
        and hasattr(request.user, 'band_profile')
        and enquiry.band == request.user.band_profile
    )
    if not is_customer and not is_manager:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Permission denied.")

    if request.method == 'POST':
        msg_text = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')
        
        if msg_text or attachment:
            EnquiryMessage.objects.create(
                enquiry=enquiry,
                sender=request.user,
                message=msg_text if msg_text else None,
                attachment=attachment
            )
            messages.success(request, 'Message sent.')
        else:
            messages.error(request, 'Please provide a message or an image.')
    return redirect('enquiries:enquiry_detail', pk=pk)


@login_required
def cancel_enquiry(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk, customer=request.user)
    if enquiry.status in ['pending', 'reviewed', 'accepted']:
        enquiry.status = 'cancelled'
        enquiry.save()
        # Notify band manager
        send_mail(
            subject=f'Enquiry Cancelled - {enquiry.reference_number}',
            message=f'The customer has cancelled enquiry {enquiry.reference_number} for {enquiry.event_date}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[enquiry.band.email],
            fail_silently=True,
        )
        messages.success(request, 'Enquiry cancelled.')
    else:
        messages.error(request, 'This enquiry cannot be cancelled.')
    return redirect('enquiries:my_enquiries')


@login_required
def manager_enquiry_list(request):
    """Band Manager: view all enquiries"""
    if request.user.role != 'band_manager':
        return redirect('core:home')
    try:
        band = request.user.band_profile
    except Exception:
        messages.error(request, 'You need to create a band profile first.')
        return redirect('bands:create_profile')

    status_filter = request.GET.get('status', '')
    enquiries = band.enquiries.select_related('customer', 'package').order_by('-created_at')
    if status_filter:
        enquiries = enquiries.filter(status=status_filter)

    return render(request, 'enquiries/manager_enquiry_list.html', {
        'enquiries': enquiries, 'status_filter': status_filter, 'band': band
    })


@login_required
def accept_enquiry(request, pk):
    """Band Manager accepts an enquiry → creates Booking + blocks date"""
    if request.user.role != 'band_manager':
        return redirect('core:home')
    enquiry = get_object_or_404(Enquiry, pk=pk, band__manager=request.user)

    if enquiry.status != 'pending' and enquiry.status != 'reviewed':
        messages.error(request, 'This enquiry cannot be accepted.')
        return redirect('enquiries:manager_enquiry_list')

    if request.method == 'GET':
        return render(request, 'enquiries/accept_enquiry.html', {'enquiry': enquiry})

    agreed_amount = request.POST.get('agreed_amount')
    payment_type = request.POST.get('payment_type', 'full')
    advance_amount = request.POST.get('advance_amount')

    if not agreed_amount or not agreed_amount.isdigit():
        messages.error(request, 'Please provide a valid agreed amount.')
        return render(request, 'enquiries/accept_enquiry.html', {'enquiry': enquiry})

    if payment_type == 'advance' and (not advance_amount or not advance_amount.isdigit()):
        messages.error(request, 'Please provide a valid advance amount.')
        return render(request, 'enquiries/accept_enquiry.html', {'enquiry': enquiry})

    # Atomic transaction: create booking + block date
    from django.db import transaction
    from bookings.models import Booking
    from bands.models import BandAvailability

    with transaction.atomic():
        # Check no existing confirmed booking
        existing = Booking.objects.filter(
            band=enquiry.band, event_date=enquiry.event_date, status__in=['pending_payment', 'confirmed']
        ).exists()
        if existing:
            messages.error(request, f'A booking already exists or is pending for {enquiry.event_date}. Cannot double-book.')
            return redirect('enquiries:manager_enquiry_list')

        enquiry.status = 'accepted'
        enquiry.save()

        booking = Booking.objects.create(
            enquiry=enquiry,
            customer=enquiry.customer,
            band=enquiry.band,
            package=enquiry.package,
            event_date=enquiry.event_date,
            event_type=enquiry.event_type,
            event_location=enquiry.event_location,
            performance_duration=enquiry.performance_duration,
            expected_audience=enquiry.expected_audience,
            agreed_amount=int(agreed_amount),
            payment_type=payment_type,
            advance_amount=int(advance_amount) if advance_amount and advance_amount.isdigit() else None,
            status='confirmed' if payment_type == 'offline' else 'pending_payment',
        )

        # Block the date atomically
        BandAvailability.objects.update_or_create(
            band=enquiry.band, date=enquiry.event_date,
            defaults={'status': 'booked'}
        )

    # Notify customer
    send_mail(
        subject=f'Booking Confirmed! - {enquiry.band.band_name} [{enquiry.reference_number}]',
        message=f'''Great news, {enquiry.customer.first_name}!

Your booking with {enquiry.band.band_name} has been ACCEPTED!

Total Agreed Amount: ₹{agreed_amount}
{f"Advance Required: ₹{advance_amount}" if payment_type == 'advance' else ""}
{f"Full Payment Required: ₹{agreed_amount}" if payment_type == 'full' else ""}
{f"Payment Type: Offline" if payment_type == 'offline' else ""}

Event: {enquiry.get_event_type_display()}
Date: {enquiry.event_date}
Location: {enquiry.event_location}
Duration: {enquiry.performance_duration} hours
Reference: {enquiry.reference_number}

{ "IMPORTANT: Your booking is NOT confirmed yet. Please log in and pay the requested amount via 'My Bookings'." if payment_type != 'offline' else "Your booking is confirmed!" }

Contact the band:
📞 {enquiry.band.phone}
📧 {enquiry.band.email}
{"📱 WhatsApp: " + enquiry.band.whatsapp if enquiry.band.whatsapp else ""}

We look forward to making your event memorable!

— Bandez''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[enquiry.customer.email],
        fail_silently=True,
    )
    if payment_type == 'offline':
        messages.success(request, f'Booking confirmed for {enquiry.event_date}! Date has been blocked.')
    else:
        messages.success(request, f'Enquiry accepted. Customer has been asked to pay via Stripe.')
    return redirect('enquiries:manager_enquiry_list')


@login_required
def reject_enquiry(request, pk):
    if request.user.role != 'band_manager':
        return redirect('core:home')
    enquiry = get_object_or_404(Enquiry, pk=pk, band__manager=request.user)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided.')
        enquiry.status = 'rejected'
        enquiry.manager_note = reason
        enquiry.save()
        send_mail(
            subject=f'Enquiry Update - {enquiry.band.band_name} [{enquiry.reference_number}]',
            message=f'''Dear {enquiry.customer.first_name},

We regret to inform you that {enquiry.band.band_name} is unable to accept your enquiry for {enquiry.event_date}.

Reason: {reason}

We encourage you to explore other talented bands on Bandez!

— Bandez''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[enquiry.customer.email],
            fail_silently=True,
        )
        messages.success(request, 'Enquiry rejected. Customer notified.')
        return redirect('enquiries:manager_enquiry_list')
    return render(request, 'enquiries/reject_enquiry.html', {'enquiry': enquiry})


def pricing_estimator_ajax(request):
    """AJAX endpoint for AI pricing estimator"""
    from core.ai_engine import estimate_price
    from bands.models import ServicePackage

    band_id = request.GET.get('band_id')
    event_type = request.GET.get('event_type', 'college')
    duration = float(request.GET.get('duration', 3))
    audience = int(request.GET.get('audience', 100))
    package_id = request.GET.get('package_id')
    location_tier = 'tier2'

    package = None
    if package_id:
        try:
            package = ServicePackage.objects.get(id=package_id)
            location_tier = package.band.location_tier
        except ServicePackage.DoesNotExist:
            pass
    elif band_id:
        try:
            band = BandProfile.objects.get(id=band_id)
            location_tier = band.location_tier
        except BandProfile.DoesNotExist:
            pass

    import datetime
    is_weekend = False
    try:
        from django.utils import timezone
        today = timezone.now().date()
        is_weekend = today.weekday() >= 5
    except Exception:
        pass

    min_price, max_price = estimate_price(
        package=package,
        event_type=event_type,
        duration=duration,
        audience=audience,
        location_tier=location_tier,
        is_weekend=is_weekend,
    )
    return JsonResponse({'min': min_price, 'max': max_price,
                         'formatted': f'₹{min_price:,} – ₹{max_price:,}'})
