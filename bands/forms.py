from django import forms
from .models import BandProfile, ServicePackage, GalleryImage, GENRE_CHOICES, EVENT_TYPE_CHOICES, LOCATION_TIER_CHOICES


class BandProfileForm(forms.ModelForm):
    genres = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'genre-checkbox'}),
        required=True
    )
    event_types = forms.MultipleChoiceField(
        choices=EVENT_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'event-type-checkbox'}),
        required=True
    )

    class Meta:
        model = BandProfile
        fields = ['band_name', 'description', 'genres', 'event_types', 'base_location',
                  'state', 'location_tier', 'phone', 'email', 'whatsapp', 'instagram_url', 'profile_photo']
        widgets = {
            'band_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Band Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your band...'}),
            'base_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'location_tier': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Band Email'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'WhatsApp Number (optional)'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/yourband'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_genres(self):
        return list(self.cleaned_data['genres'])

    def clean_event_types(self):
        return list(self.cleaned_data['event_types'])


class ServicePackageForm(forms.ModelForm):
    class Meta:
        model = ServicePackage
        fields = ['name', 'description', 'min_price', 'max_price', 'duration_hours']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Basic, Standard, Premium'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'min_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Price (INR)'}),
            'max_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Price (INR)'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hours', 'step': '0.5'}),
        }


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caption (optional)'}),
        }


class AvailabilityForm(forms.Form):
    dates = forms.CharField(widget=forms.HiddenInput())
    status = forms.ChoiceField(choices=[('available', 'Mark Available'), ('blocked', 'Mark Blocked')],
                               widget=forms.Select(attrs={'class': 'form-select'}))
