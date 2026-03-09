from django import forms
from .models import Enquiry, EVENT_TYPE_CHOICES, CONTACT_METHOD_CHOICES
from bands.models import ServicePackage


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['event_type', 'event_date', 'event_location', 'performance_duration',
                  'expected_audience', 'package',
                  'message', 'preferred_contact']
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'event_date_picker'}),
            'event_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where will the event be held?'}),
            'performance_duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hours', 'step': '0.5', 'min': '1'}),
            'expected_audience': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Approximate number of guests'}),
            'package': forms.Select(attrs={'class': 'form-select'}),

            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your requirements, special requests, or any other details...'}),
            'preferred_contact': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, band=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if band:
            self.fields['package'].queryset = ServicePackage.objects.filter(band=band, is_active=True)
            self.fields['package'].required = False
            self.fields['package'].empty_label = '-- Select a package (optional) --'
