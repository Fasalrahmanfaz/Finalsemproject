from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Rating
from bands.models import BandProfile
from bookings.models import Booking


@login_required
def submit_rating(request, booking_pk):
    """Customer submits rating after booking is completed"""
    booking = get_object_or_404(Booking, pk=booking_pk, customer=request.user, status='completed')

    # Check already rated
    if hasattr(booking, 'rating'):
        messages.info(request, 'You have already rated this band.')
        return redirect('bookings:my_bookings')

    if request.method == 'POST':
        stars = int(request.POST.get('stars', 0))
        review = request.POST.get('review', '').strip()
        if not (1 <= stars <= 5):
            messages.error(request, 'Please select a rating between 1 and 5 stars.')
            return render(request, 'reviews/rate.html', {'booking': booking})
        Rating.objects.create(
            customer=request.user,
            band=booking.band,
            booking=booking,
            stars=stars,
            review=review,
            event_type=booking.event_type,
        )
        messages.success(request, f'Thank you for rating {booking.band.band_name}! Your review helps others.')
        return redirect('bookings:my_bookings')

    return render(request, 'reviews/rate.html', {'booking': booking})


@login_required
def delete_review(request, pk):
    """Admin can delete any review; customer can delete their own"""
    review = get_object_or_404(Rating, pk=pk)
    if request.user.role == 'admin' or request.user.is_staff or review.customer == request.user:
        band = review.band
        review.delete()
        messages.success(request, 'Review deleted.')
        if request.user.role == 'admin' or request.user.is_staff:
            return redirect('core:admin_dashboard')
        return redirect('bands:profile_detail', pk=band.pk)
    messages.error(request, 'Permission denied.')
    return redirect('core:home')


def band_reviews(request, band_pk):
    """View all reviews for a band"""
    band = get_object_or_404(BandProfile, pk=band_pk)
    reviews = band.ratings.filter(is_approved=True).select_related('customer')
    return render(request, 'reviews/band_reviews.html', {'band': band, 'reviews': reviews})


@login_required
def rate_band(request, band_pk):
    """Any logged-in customer can rate a band"""
    if request.user.role != 'customer':
        messages.error(request, 'Only customers can rate bands.')
        return redirect('bands:profile_detail', pk=band_pk)

    band = get_object_or_404(BandProfile, pk=band_pk, is_active=True)

    # Check if already rated this band
    existing = Rating.objects.filter(customer=request.user, band=band).first()
    if existing:
        messages.info(request, 'You have already rated this band.')
        return redirect('bands:profile_detail', pk=band_pk)

    if request.method == 'POST':
        stars = int(request.POST.get('stars', 0))
        review = request.POST.get('review', '').strip()
        if not (1 <= stars <= 5):
            messages.error(request, 'Please select a rating between 1 and 5 stars.')
            return render(request, 'reviews/rate_band.html', {'band': band})
        Rating.objects.create(
            customer=request.user,
            band=band,
            stars=stars,
            review=review,
        )
        messages.success(request, f'Thank you for rating {band.band_name}!')
        return redirect('bands:profile_detail', pk=band_pk)

    return render(request, 'reviews/rate_band.html', {'band': band})
