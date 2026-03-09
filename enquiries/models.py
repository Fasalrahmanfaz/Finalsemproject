from django.db import models
from accounts.models import User
from bands.models import BandProfile, ServicePackage


ENQUIRY_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('reviewed', 'Reviewed'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

ENQUIRY_CATEGORY_CHOICES = [
    ('booking_request', 'Booking Request'),
    ('price_enquiry', 'Price Enquiry'),
    ('availability_enquiry', 'Availability Enquiry'),
    ('general_information', 'General Information'),
    ('complaint', 'Complaint'),
]

EVENT_TYPE_CHOICES = [
    ('wedding', 'Wedding'),
    ('college', 'College Programs'),
    ('school', 'School Events'),
    ('corporate', 'Corporate Events'),
    ('private', 'Private Functions'),
]

CONTACT_METHOD_CHOICES = [
    ('phone', 'Phone Call'),
    ('email', 'Email'),
    ('whatsapp', 'WhatsApp'),
]


class Enquiry(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enquiries')
    band = models.ForeignKey(BandProfile, on_delete=models.CASCADE, related_name='enquiries')
    package = models.ForeignKey(ServicePackage, on_delete=models.SET_NULL, null=True, blank=True)
    reference_number = models.CharField(max_length=20, unique=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    event_date = models.DateField()
    event_location = models.CharField(max_length=300)
    performance_duration = models.FloatField(help_text="Hours")
    expected_audience = models.IntegerField()

    message = models.TextField()
    preferred_contact = models.CharField(max_length=10, choices=CONTACT_METHOD_CHOICES, default='email')
    ai_category = models.CharField(max_length=30, choices=ENQUIRY_CATEGORY_CHOICES, default='general_information')
    ai_confidence = models.FloatField(default=0.0)
    status = models.CharField(max_length=15, choices=ENQUIRY_STATUS_CHOICES, default='pending')
    manager_note = models.TextField(blank=True)
    auto_reply_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def generate_reference(self):
        import random, string
        return 'BNZ' + ''.join(random.choices(string.digits, k=8))

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self.generate_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number} - {self.customer} → {self.band.band_name}"


class EnquiryMessage(models.Model):
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    attachment = models.ImageField(upload_to='message_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender} on {self.enquiry.reference_number}"
