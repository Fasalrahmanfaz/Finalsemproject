from django.contrib import admin
from .models import BandProfile, ServicePackage, GalleryImage, BandAvailability


@admin.register(BandProfile)
class BandProfileAdmin(admin.ModelAdmin):
    list_display = ['band_name', 'manager', 'base_location', 'is_active', 'is_approved', 'average_rating', 'events_attended', 'created_at']
    list_filter = ['is_active', 'is_approved', 'location_tier']
    search_fields = ['band_name', 'base_location', 'manager__email']
    actions = ['approve_profiles', 'suspend_profiles']

    def approve_profiles(self, request, queryset):
        queryset.update(is_approved=True, is_active=True)
    approve_profiles.short_description = "Approve selected band profiles"

    def suspend_profiles(self, request, queryset):
        queryset.update(is_active=False)
    suspend_profiles.short_description = "Suspend selected band profiles"


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'band', 'min_price', 'max_price', 'duration_hours', 'is_active']
    list_filter = ['is_active']


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['band', 'caption', 'order', 'uploaded_at']


@admin.register(BandAvailability)
class BandAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['band', 'date', 'status', 'note']
    list_filter = ['status']
    search_fields = ['band__band_name']
