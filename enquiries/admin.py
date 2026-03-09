from django.contrib import admin
from .models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'customer', 'band', 'event_type', 'event_date', 'ai_category', 'status', 'created_at']
    list_filter = ['status', 'ai_category', 'event_type']
    search_fields = ['reference_number', 'customer__email', 'band__band_name']
    readonly_fields = ['reference_number', 'ai_category', 'ai_confidence']
