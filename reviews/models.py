from django.db import models
from accounts.models import User
from bands.models import BandProfile
from bookings.models import Booking
from django.core.validators import MinValueValidator, MaxValueValidator


class Rating(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    band = models.ForeignKey(BandProfile, on_delete=models.CASCADE, related_name='ratings')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='rating', null=True, blank=True)
    stars = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.band.update_rating()

    def delete(self, *args, **kwargs):
        band = self.band
        super().delete(*args, **kwargs)
        band.update_rating()

    def __str__(self):
        return f"{self.customer} rated {self.band.band_name}: {self.stars}★"
