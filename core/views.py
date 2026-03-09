from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone


def home(request):
    """Home/landing page"""
    from bands.models import BandProfile, GalleryImage
    from bands.views import get_recommendations
    featured_bands = BandProfile.objects.filter(is_active=True, is_approved=True).order_by('-average_rating')[:6]
    gallery_images = GalleryImage.objects.filter(band__is_active=True).order_by('?')[:8]
    top_rated = BandProfile.objects.filter(is_active=True, is_approved=True, total_reviews__gt=0).order_by('-average_rating')[:3]
    total_bands = BandProfile.objects.filter(is_active=True).count()
    return render(request, 'core/home.html', {
        'featured_bands': featured_bands,
        'gallery_images': gallery_images,
        'top_rated': top_rated,
        'total_bands': total_bands,
    })


@login_required
def customer_dashboard(request):
    if request.user.role not in ['customer']:
        return redirect('core:home')
    from enquiries.models import Enquiry
    from bookings.models import Booking
    enquiries = request.user.enquiries.order_by('-created_at')[:5]
    bookings = request.user.bookings.order_by('-event_date')[:5]
    upcoming = request.user.bookings.filter(status='confirmed', event_date__gte=timezone.now().date()).order_by('event_date').first()
    stats = {
        'total_enquiries': request.user.enquiries.count(),
        'pending': request.user.enquiries.filter(status='pending').count(),
        'accepted': request.user.enquiries.filter(status='accepted').count(),
        'completed': request.user.bookings.filter(status='completed').count(),
    }
    return render(request, 'core/customer_dashboard.html', {
        'enquiries': enquiries, 'bookings': bookings, 'upcoming': upcoming, 'stats': stats
    })


@login_required
def admin_dashboard(request):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')

    from accounts.models import User
    from bands.models import BandProfile
    from enquiries.models import Enquiry
    from bookings.models import Booking
    from reviews.models import Rating

    stats = {
        'total_users': User.objects.filter(role='customer').count(),
        'total_managers': User.objects.filter(role='band_manager').count(),
        'total_bands': BandProfile.objects.count(),
        'active_bands': BandProfile.objects.filter(is_active=True, is_approved=True).count(),
        'total_enquiries': Enquiry.objects.count(),
        'total_bookings': Booking.objects.count(),
        'completed_events': Booking.objects.filter(status='completed').count(),
        'total_reviews': Rating.objects.count(),
    }

    # Enquiry category breakdown
    from django.db.models import Count
    enquiry_categories = Enquiry.objects.values('ai_category').annotate(count=Count('id'))

    # Recent data
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_bands = BandProfile.objects.order_by('-created_at')[:10]
    recent_enquiries = Enquiry.objects.select_related('customer', 'band').order_by('-created_at')[:10]
    pending_bands = BandProfile.objects.filter(is_approved=False)
    recent_reviews = Rating.objects.select_related('customer', 'band').order_by('-created_at')[:10]

    return render(request, 'core/admin_dashboard.html', {
        'stats': stats,
        'enquiry_categories': list(enquiry_categories),
        'recent_users': recent_users,
        'recent_bands': recent_bands,
        'recent_enquiries': recent_enquiries,
        'pending_bands': pending_bands,
        'recent_reviews': recent_reviews,
    })


@login_required
def admin_users(request):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from accounts.models import User
    users = User.objects.all().order_by('-date_joined')
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    return render(request, 'core/admin_users.html', {'users': users, 'role_filter': role_filter})


@login_required
def admin_toggle_user(request, pk):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from accounts.models import User
    user = User.objects.get(pk=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save()
    return redirect('core:admin_users')


@login_required
def admin_bands(request):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from bands.models import BandProfile
    bands = BandProfile.objects.select_related('manager').order_by('-created_at')
    return render(request, 'core/admin_bands.html', {'bands': bands})


@login_required
def admin_approve_band(request, pk):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from bands.models import BandProfile
    band = BandProfile.objects.get(pk=pk)
    band.is_approved = True
    band.is_active = True
    band.save()
    return redirect('core:admin_bands')


@login_required
def admin_toggle_band(request, pk):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from bands.models import BandProfile
    band = BandProfile.objects.get(pk=pk)
    band.is_active = not band.is_active
    band.save()
    return redirect('core:admin_bands')


@login_required
def admin_enquiries(request):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from enquiries.models import Enquiry
    enquiries = Enquiry.objects.select_related('customer', 'band').order_by('-created_at')
    return render(request, 'core/admin_enquiries.html', {'enquiries': enquiries})


@login_required
def admin_reviews(request):
    if not (request.user.role == 'admin' or request.user.is_staff):
        return redirect('core:home')
    from reviews.models import Rating
    reviews = Rating.objects.select_related('customer', 'band').order_by('-created_at')
    return render(request, 'core/admin_reviews.html', {'reviews': reviews})


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')
