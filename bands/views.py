from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models as db_models
from django.utils import timezone
from PIL import Image
import os
import json
from .models import BandProfile, ServicePackage, GalleryImage, BandAvailability
from .forms import BandProfileForm, ServicePackageForm, GalleryImageForm, AvailabilityForm
from django.conf import settings


def get_calendar_events(band, is_manager=False, include_past=False):
    from datetime import timedelta
    events = []
    color_map = {'available': '#28a745', 'booked': '#dc3545', 'blocked': '#6c757d', 'pending': '#ffc107'}
    
    # Explicit availability
    availability = band.availability.all() if include_past else band.availability.filter(date__gte=timezone.now().date())
    explicit_dates = set()
    for a in availability:
        explicit_dates.add(str(a.date))
        events.append({
            'title': a.note if a.note else a.get_status_display(),
            'start': str(a.date),
            'color': color_map.get(a.status, '#6c757d'),
            'status': a.status,
        })
        
    # Bookings
    from bookings.models import Booking
    q = Booking.objects.filter(band=band, status='confirmed')
    if not include_past:
        q = q.filter(event_date__gte=timezone.now().date())
        
    for b in q:
        date_str = str(b.event_date)
        if date_str not in explicit_dates:
            title = f'Event: {b.event_type}' if is_manager else 'Booked'
            events.append({
                'title': title,
                'start': date_str,
                'color': '#dc3545',
                'status': 'booked',
            })
            explicit_dates.add(date_str)
            
    # Implicit availability (next 90 days)
    today = timezone.now().date()
    for i in range(90):
        d_str = str(today + timedelta(days=i))
        if d_str not in explicit_dates:
            events.append({
                'title': 'Available',
                'start': d_str,
                'color': '#28a745',
                'status': 'available',
            })
            
    return events

def explore(request):
    """Public explore/browse page"""
    bands = BandProfile.objects.filter(is_active=True, is_approved=True)
    query = request.GET.get('q', '')
    event_type = request.GET.get('event_type', 'all')
    genre = request.GET.get('genre', '')
    location = request.GET.get('location', '')
    min_rating = request.GET.get('min_rating', '')
    sort_by = request.GET.get('sort', 'newest')

    if query:
        bands = bands.filter(
            db_models.Q(band_name__icontains=query) |
            db_models.Q(base_location__icontains=query) |
            db_models.Q(description__icontains=query)
        )

    if event_type and event_type != 'all':
        # Filter bands that have this event type in their JSON list
        all_bands = list(bands)
        bands_filtered = [b for b in all_bands if event_type in (b.event_types or [])]
        band_ids = [b.id for b in bands_filtered]
        bands = BandProfile.objects.filter(id__in=band_ids, is_active=True, is_approved=True)

    if genre:
        all_bands = list(bands)
        bands_filtered = [b for b in all_bands if genre in (b.genres or [])]
        band_ids = [b.id for b in bands_filtered]
        bands = BandProfile.objects.filter(id__in=band_ids, is_active=True, is_approved=True)

    if location:
        bands = bands.filter(base_location__icontains=location)

    if min_rating:
        try:
            bands = bands.filter(average_rating__gte=float(min_rating))
        except ValueError:
            pass

    sort_map = {
        'rating': '-average_rating',
        'events': '-events_attended',
        'newest': '-created_at',
        'alphabetical': 'band_name',
    }
    bands = bands.order_by(sort_map.get(sort_by, '-created_at'))

    # Recommendation engine for top picks
    top_picks = get_recommendations(event_type=event_type, exclude_ids=[])[:6]

    # Gallery images for the explore page mosaic
    gallery_images = GalleryImage.objects.filter(band__is_active=True, band__is_approved=True).order_by('?')[:12]

    from .models import GENRE_CHOICES, EVENT_TYPE_CHOICES
    context = {
        'bands': bands,
        'top_picks': top_picks,
        'gallery_images': gallery_images,
        'query': query,
        'event_type': event_type,
        'genre': genre,
        'location': location,
        'min_rating': min_rating,
        'sort_by': sort_by,
        'genre_choices': GENRE_CHOICES,
        'event_type_choices': EVENT_TYPE_CHOICES,
    }
    return render(request, 'bands/explore.html', context)


def band_profile_detail(request, pk):
    """Public band profile page"""
    band = get_object_or_404(BandProfile, pk=pk, is_active=True, is_approved=True)
    packages = band.packages.filter(is_active=True)
    gallery = band.gallery_images.order_by('order')
    availability = band.availability.filter(date__gte=timezone.now().date())
    reviews = band.ratings.filter(is_approved=True).select_related('customer')

    # Star distribution
    star_distribution = []
    total_reviews = reviews.count()
    for i in range(5, 0, -1):
        count = reviews.filter(stars=i).count()
        star_distribution.append({'stars': i, 'count': count, 'pct': round(count / total_reviews * 100) if total_reviews > 0 else 0})

    # Recommendations
    similar_bands = get_recommendations(
        event_types=band.event_types,
        location=band.base_location,
        exclude_ids=[band.id]
    )[:4]

    # Availability calendar data
    avail_data = get_calendar_events(band, is_manager=False)

    context = {
        'band': band,
        'packages': packages,
        'gallery': gallery,
        'availability_json': json.dumps(avail_data),
        'reviews': reviews,
        'star_distribution': star_distribution,
        'similar_bands': similar_bands,
        'total_reviews': total_reviews,
    }
    return render(request, 'bands/profile_detail.html', context)


def get_recommendations(event_type=None, event_types=None, location=None, exclude_ids=None, limit=6):
    """Band recommendation engine using 5-factor weighted scoring"""
    exclude_ids = exclude_ids or []
    bands = BandProfile.objects.filter(is_active=True, is_approved=True).exclude(id__in=exclude_ids)
    scored = []
    for band in bands:
        score = 0
        # 1. Event type match (40%)
        et_types = event_types or ([event_type] if event_type and event_type != 'all' else [])
        if et_types:
            matches = sum(1 for et in et_types if et in (band.event_types or []))
            score += (matches / max(len(et_types), 1)) * 40
        else:
            score += 20
        # 2. Location match (25%)
        if location and band.base_location:
            if location.lower() in band.base_location.lower() or band.base_location.lower() in (location or '').lower():
                score += 25
        # 3. Average star rating (20%)
        score += (band.average_rating / 5) * 20
        # 4. Events attended (10%)
        events_score = min(band.events_attended / 100, 1.0) * 10
        score += events_score
        # 5. Genre diversity (5%)
        score += min(len(band.genres or []) / 5, 1.0) * 5
        scored.append((score, band))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:limit]]


@login_required
def manager_dashboard(request):
    """Band Manager Dashboard"""
    if request.user.role != 'band_manager':
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    try:
        band = request.user.band_profile
    except BandProfile.DoesNotExist:
        band = None

    if band:
        from enquiries.models import Enquiry
        enquiries = band.enquiries.all().order_by('-created_at')
        upcoming_bookings = band.bookings.filter(
            status='confirmed',
            event_date__gte=timezone.now().date()
        ).order_by('event_date')

        # Stats
        stats = {
            'total_enquiries': enquiries.count(),
            'pending': enquiries.filter(status='pending').count(),
            'accepted': enquiries.filter(status='accepted').count(),
            'completed': enquiries.filter(status='completed').count(),
        }
        # Calendar data
        avail_data = get_calendar_events(band, is_manager=True)
        context = {
            'band': band,
            'enquiries': enquiries[:10],
            'recent_enquiries': enquiries[:10],
            'upcoming_bookings': upcoming_bookings[:5],
            'stats': stats,
            'pending_enquiries_count': stats['pending'],
            'total_bookings_count': band.bookings.count(),
            'availability_json': json.dumps(avail_data),
        }
    else:
        context = {'band': None}

    return render(request, 'bands/manager_dashboard.html', context)


@login_required
def create_band_profile(request):
    if request.user.role != 'band_manager':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    if hasattr(request.user, 'band_profile'):
        messages.info(request, 'You already have a band profile.')
        return redirect('bands:edit_profile')

    if request.method == 'POST':
        form = BandProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.manager = request.user
            if profile.profile_photo:
                profile.profile_photo = resize_image(profile.profile_photo)
            profile.save()
            messages.success(request, 'Band profile created! Now add your service packages and gallery images.')
            return redirect('bands:manager_dashboard')
    else:
        form = BandProfileForm()
    return render(request, 'bands/create_profile.html', {'form': form})


@login_required
def edit_band_profile(request):
    if request.user.role != 'band_manager':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    band = get_object_or_404(BandProfile, manager=request.user)
    if request.method == 'POST':
        form = BandProfileForm(request.POST, request.FILES, instance=band)
        if form.is_valid():
            profile = form.save(commit=False)
            if 'profile_photo' in request.FILES:
                profile.profile_photo = resize_image(profile.profile_photo)
            profile.save()
            messages.success(request, 'Band profile updated successfully!')
            return redirect('bands:manager_dashboard')
    else:
        form = BandProfileForm(instance=band, initial={
            'genres': band.genres,
            'event_types': band.event_types,
        })
    return render(request, 'bands/edit_profile.html', {'form': form, 'band': band})


def resize_image(image_field):
    """Resize image using Pillow"""
    from io import BytesIO
    from django.core.files.uploadedfile import InMemoryUploadedFile
    img = Image.open(image_field)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    max_size = (800, 800)
    img.thumbnail(max_size, Image.LANCZOS)
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    return InMemoryUploadedFile(
        output, 'ImageField', image_field.name, 'image/jpeg', output.getbuffer().nbytes, None
    )


# --- Service Packages ---
@login_required
def manage_packages(request):
    band = get_object_or_404(BandProfile, manager=request.user)
    packages = band.packages.all()
    return render(request, 'bands/packages.html', {'band': band, 'packages': packages})


@login_required
def add_package(request):
    band = get_object_or_404(BandProfile, manager=request.user)
    if request.method == 'POST':
        form = ServicePackageForm(request.POST)
        if form.is_valid():
            pkg = form.save(commit=False)
            pkg.band = band
            pkg.save()
            messages.success(request, 'Package added!')
            return redirect('bands:manage_packages')
    else:
        form = ServicePackageForm()
    return render(request, 'bands/package_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_package(request, pk):
    band = get_object_or_404(BandProfile, manager=request.user)
    pkg = get_object_or_404(ServicePackage, pk=pk, band=band)
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, instance=pkg)
        if form.is_valid():
            form.save()
            messages.success(request, 'Package updated!')
            return redirect('bands:manage_packages')
    else:
        form = ServicePackageForm(instance=pkg)
    return render(request, 'bands/package_form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_package(request, pk):
    band = get_object_or_404(BandProfile, manager=request.user)
    pkg = get_object_or_404(ServicePackage, pk=pk, band=band)
    pkg.delete()
    messages.success(request, 'Package deleted.')
    return redirect('bands:manage_packages')


# --- Gallery ---
@login_required
def manage_gallery(request):
    band = get_object_or_404(BandProfile, manager=request.user)
    images = band.gallery_images.order_by('order')
    max_images = settings.MAX_GALLERY_IMAGES
    return render(request, 'bands/gallery_manage.html', {
        'band': band, 'images': images, 'max_images': max_images
    })


@login_required
def upload_gallery_image(request):
    band = get_object_or_404(BandProfile, manager=request.user)
    if band.gallery_images.count() >= settings.MAX_GALLERY_IMAGES:
        messages.error(request, f'Maximum {settings.MAX_GALLERY_IMAGES} gallery images allowed.')
        return redirect('bands:manage_gallery')
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.band = band
            img.order = band.gallery_images.count()
            img.save()
            messages.success(request, 'Image uploaded successfully!')
            return redirect('bands:manage_gallery')
    else:
        form = GalleryImageForm()
    return render(request, 'bands/gallery_upload.html', {'form': form})


@login_required
def delete_gallery_image(request, pk):
    band = get_object_or_404(BandProfile, manager=request.user)
    img = get_object_or_404(GalleryImage, pk=pk, band=band)
    # Delete the file
    if img.image and os.path.exists(img.image.path):
        os.remove(img.image.path)
    img.delete()
    # Reorder
    for i, image in enumerate(band.gallery_images.order_by('order')):
        image.order = i
        image.save()
    messages.success(request, 'Image deleted.')
    return redirect('bands:manage_gallery')


@login_required
def reorder_gallery(request):
    """AJAX endpoint to reorder gallery images"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_list = data.get('order', [])
            band = get_object_or_404(BandProfile, manager=request.user)
            for idx, img_id in enumerate(order_list):
                GalleryImage.objects.filter(id=img_id, band=band).update(order=idx)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


# --- Availability Calendar ---
@login_required
def manage_availability(request):
    band = get_object_or_404(BandProfile, manager=request.user)
    form = AvailabilityForm()

    if request.method == 'POST':
        content_type = request.content_type or ''
        if 'application/json' in content_type:
            # AJAX JSON request
            try:
                data = json.loads(request.body)
                dates = data.get('dates', [])
                status = data.get('status', 'available')
                note = data.get('note', '')
                for date_str in dates:
                    BandAvailability.objects.update_or_create(
                        band=band, date=date_str,
                        defaults={'status': status, 'note': note}
                    )
                return JsonResponse({'success': True, 'message': f'{len(dates)} dates updated.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            # Regular HTML form POST
            form = AvailabilityForm(request.POST)
            if form.is_valid():
                avail = form.save(commit=False)
                avail.band = band
                avail.save()
                messages.success(request, 'Availability updated successfully!')
                return redirect('bands:manage_availability')

    avail_data = get_calendar_events(band, is_manager=True, include_past=True)
    return render(request, 'bands/availability.html', {
        'band': band,
        'form': form,
        'availability_json': json.dumps(avail_data),
    })


def check_availability_ajax(request):
    """AJAX: check if band is available on a date"""
    band_id = request.GET.get('band_id')
    date_str = request.GET.get('date')
    if not band_id or not date_str:
        return JsonResponse({'available': False, 'message': 'Missing parameters'})

    from datetime import datetime
    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'available': False, 'message': 'Invalid date format'})

    band = get_object_or_404(BandProfile, pk=band_id)

    # Check if date is blocked or booked
    avail = BandAvailability.objects.filter(band=band, date=check_date).first()
    from bookings.models import Booking
    has_booking = Booking.objects.filter(band=band, event_date=check_date, status='confirmed').exists()

    if has_booking or (avail and avail.status in ['booked', 'blocked']):
        # Find nearest 3 available dates
        from datetime import timedelta
        nearest = []
        for delta in range(1, 22):
            for direction in [-1, 1]:
                candidate = check_date + timedelta(days=delta * direction)
                if candidate < timezone.now().date():
                    continue
                candidate_avail = BandAvailability.objects.filter(band=band, date=candidate).first()
                candidate_booked = Booking.objects.filter(band=band, event_date=candidate, status='confirmed').exists()
                if not candidate_booked and (not candidate_avail or candidate_avail.status == 'available'):
                    if str(candidate) not in nearest:
                        nearest.append(str(candidate))
                if len(nearest) >= 3:
                    break
            if len(nearest) >= 3:
                break

        # Suggest alternative bands available on the same date
        alternative_bands = []
        similar = get_recommendations(
            event_types=band.event_types,
            location=band.base_location,
            exclude_ids=[band.id],
            limit=10
        )
        for alt_band in similar:
            alt_avail = BandAvailability.objects.filter(band=alt_band, date=check_date).first()
            alt_booked = Booking.objects.filter(band=alt_band, event_date=check_date, status='confirmed').exists()
            if not alt_booked and (not alt_avail or alt_avail.status == 'available'):
                alternative_bands.append({
                    'id': alt_band.id,
                    'name': alt_band.band_name,
                    'location': alt_band.base_location,
                    'rating': float(alt_band.average_rating),
                    'photo': alt_band.profile_photo.url if alt_band.profile_photo else '',
                })
            if len(alternative_bands) >= 3:
                break

        return JsonResponse({
            'available': False,
            'message': 'Not available on this date.',
            'nearest_dates': nearest[:3],
            'alternative_bands': alternative_bands,
        })
    else:
        return JsonResponse({'available': True, 'message': 'This date is available! ✓'})


def get_availability_calendar_ajax(request, band_id):
    """AJAX: return calendar data for a band"""
    band = get_object_or_404(BandProfile, pk=band_id)
    events = get_calendar_events(band, is_manager=False, include_past=True)
    return JsonResponse(events, safe=False)


@login_required
def delete_band(request):
    """Allow band managers to delete their band profile."""
    if request.user.role != 'band_manager':
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    band = get_object_or_404(BandProfile, manager=request.user)
    if request.method == 'POST':
        band_name = band.band_name
        band.delete()
        messages.success(request, f'Band profile "{band_name}" has been permanently deleted.')
        return redirect('bands:manager_dashboard')
    return render(request, 'bands/delete_band.html', {'band': band})
