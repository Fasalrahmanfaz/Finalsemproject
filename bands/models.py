from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


GENRE_CHOICES = [
    ('carnatic', 'Carnatic'),
    ('bollywood', 'Bollywood'),
    ('jazz', 'Jazz'),
    ('rock', 'Rock'),
    ('pop', 'Pop'),
    ('folk', 'Folk'),
    ('classical', 'Classical'),
    ('western', 'Western'),
    ('fusion', 'Fusion'),
    ('devotional', 'Devotional'),
    ('instrumental', 'Instrumental'),
    ('electronic', 'Electronic'),
]

EVENT_TYPE_CHOICES = [
    ('wedding', 'Wedding'),
    ('college', 'College Programs'),
    ('school', 'School Events'),
    ('corporate', 'Corporate Events'),
    ('private', 'Private Functions'),
]

LOCATION_TIER_CHOICES = [
    ('metro', 'Metro City'),
    ('tier1', 'Tier-1 City'),
    ('tier2', 'Tier-2 City'),
    ('rural', 'Rural'),
]


class BandProfile(models.Model):
    manager = models.OneToOneField(User, on_delete=models.CASCADE, related_name='band_profile')
    band_name = models.CharField(max_length=200)
    description = models.TextField()
    genres = models.JSONField(default=list)  # list of genre keys
    event_types = models.JSONField(default=list)  # list of event type keys
    base_location = models.CharField(max_length=200)
    state = models.CharField(max_length=100, blank=True)
    location_tier = models.CharField(max_length=10, choices=LOCATION_TIER_CHOICES, default='tier2')
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    whatsapp = models.CharField(max_length=15, blank=True)
    instagram_url = models.URLField(blank=True)
    profile_photo = models.ImageField(upload_to='band_profiles/', blank=True, null=True)
    events_attended = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_genres_display_list(self):
        genre_map = dict(GENRE_CHOICES)
        return [genre_map.get(g, g) for g in self.genres]

    def get_event_types_display_list(self):
        et_map = dict(EVENT_TYPE_CHOICES)
        return [et_map.get(e, e) for e in self.event_types]

    def get_thumbnail(self):
        return self.profile_photo

    def update_rating(self):
        from reviews.models import Rating
        ratings = Rating.objects.filter(band=self)
        if ratings.exists():
            total = sum(r.stars for r in ratings)
            self.average_rating = round(total / ratings.count(), 1)
            self.total_reviews = ratings.count()
        else:
            self.average_rating = 0.0
            self.total_reviews = 0
        self.save()

    def __str__(self):
        return self.band_name


class ServicePackage(models.Model):
    band = models.ForeignKey(BandProfile, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_price = models.IntegerField(validators=[MinValueValidator(0)])
    max_price = models.IntegerField(validators=[MinValueValidator(0)])
    duration_hours = models.FloatField(validators=[MinValueValidator(0.5)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.band.band_name} - {self.name}"


class GalleryImage(models.Model):
    band = models.ForeignKey(BandProfile, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='band_gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.band.band_name} - Image {self.order}"


class BandAvailability(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('blocked', 'Blocked'),
        ('booked', 'Booked'),
        ('pending', 'Pending'),
    ]
    band = models.ForeignKey(BandProfile, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['band', 'date']
        ordering = ['date']

    def __str__(self):
        return f"{self.band.band_name} - {self.date} ({self.status})"
