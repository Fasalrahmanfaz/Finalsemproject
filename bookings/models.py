from django.db import models
from accounts.models import User
from bands.models import BandProfile, ServicePackage
from enquiries.models import Enquiry


BOOKING_STATUS_CHOICES = [
    ('pending_payment', 'Pending Payment'),
    ('confirmed', 'Confirmed'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

PAYMENT_TYPE_CHOICES = [
    ('full', 'Full Amount'),
    ('advance', 'Advance Amount'),
    ('offline', 'Offline (Pay Later)'),
]


class Booking(models.Model):
    enquiry = models.OneToOneField(Enquiry, on_delete=models.CASCADE, related_name='booking')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    band = models.ForeignKey(BandProfile, on_delete=models.CASCADE, related_name='bookings')
    package = models.ForeignKey(ServicePackage, on_delete=models.SET_NULL, null=True, blank=True)
    event_date = models.DateField()
    event_type = models.CharField(max_length=20)
    event_location = models.CharField(max_length=300)
    performance_duration = models.FloatField()
    expected_audience = models.IntegerField()
    agreed_amount = models.IntegerField(null=True, blank=True)
    payment_type = models.CharField(max_length=15, choices=PAYMENT_TYPE_CHOICES, default='full')
    advance_amount = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending_payment')
    
    # Payment tracking fields
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='pending')
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)

    reminder_sent = models.BooleanField(default=False)
    rating_prompt_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-event_date']

    def __str__(self):
        return f"Booking: {self.customer} | {self.band.band_name} | {self.event_date}"
