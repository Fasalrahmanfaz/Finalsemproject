from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['enquiry', 'customer', 'band', 'event_date', 'status', 'created_at']
    list_filter = ['status', 'event_type']
    search_fields = ['customer__email', 'band__band_name']
