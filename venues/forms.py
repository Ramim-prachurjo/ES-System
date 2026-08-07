from django import forms
from .models import Venue, VenueBooking

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'address', 'city', 'capacity', 'rental_fee', 'description', 'photo', 'is_available']
        widgets = {
            # The current Cloudinary URL is shown separately in the edit UI.
            # FileInput avoids Django's confusing default URL / Clear checkbox.
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class BookingRequestForm(forms.ModelForm):

    class Meta:
        model  = VenueBooking
        fields = ['start_date', 'end_date']
        widgets = {
            # date picker only — no time
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # we pass venue in from the view so we can check conflicts
        self.venue = kwargs.pop('venue', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end   = cleaned_data.get('end_date')

        if not start or not end:
            return cleaned_data

        # end must be same day or after start
        if end < start:
            raise forms.ValidationError("End date must be on or after the start date.")

        # ── conflict check ──
        # find any booking for this venue that overlaps the requested range
        if self.venue:
            conflict = VenueBooking.objects.filter(
                venue=self.venue,
                status__in=['pending', 'confirmed'],
                start_date__lte=end,    # existing booking starts before our end
                end_date__gte=start,    # existing booking ends after our start
            ).exists()

            if conflict:
                raise forms.ValidationError(
                    "These dates overlap with an existing booking for this venue. "
                    "Please choose different dates."
                )

        return cleaned_data
