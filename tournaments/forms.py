from django import forms
from .models import Tournament
from venues.models import Venue, VenueBooking


GAME_CHOICES = [
    ('valorant', 'Valorant'),
    ('pubg',     'PUBG'),
]


class TournamentForm(forms.ModelForm):

    # multiple checkbox selection for games
    games = forms.MultipleChoiceField(
        choices=GAME_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select one or both games',
    )

    class Meta:
        model  = Tournament
        fields = [
            'name', 'description', 'rules',
            'needs_venue', 'venue', 'venue_address', 'games',
            'start_date', 'end_date', 'registration_deadline',
            'max_teams', 'entry_fee', 'prize_pool',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['needs_venue'].widget = forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')])
        self.fields['venue'].required = False
        self.fields['venue_address'].required = False
        self.fields['venue'].queryset = Venue.objects.filter(is_available=True).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end   = cleaned_data.get('end_date')

        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date.")
        venue = cleaned_data.get('venue')
        if cleaned_data.get('needs_venue') and not venue:
            self.add_error('venue', 'Select an available venue.')
        if not cleaned_data.get('needs_venue') and not cleaned_data.get('venue_address', '').strip():
            self.add_error('venue_address', 'Enter the venue address.')
        if venue and start and end and VenueBooking.objects.filter(venue=venue, status__in=['pending', 'confirmed'], start_date__lte=end, end_date__gte=start).exists():
            self.add_error('venue', 'This venue is unavailable for those dates.')

        return cleaned_data

    def clean_games(self):
        # join list ['valorant','pubg'] → "valorant,pubg" for storage
        return ','.join(self.cleaned_data['games'])

