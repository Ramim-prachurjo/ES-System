from django import forms
from .models import Tournament


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
            'venue', 'games',
            'start_date', 'end_date',
            'max_teams', 'entry_fee', 'prize_pool',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end   = cleaned_data.get('end_date')

        if start and end and end < start:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data

    def clean_games(self):
        # join list ['valorant','pubg'] → "valorant,pubg" for storage
        return ','.join(self.cleaned_data['games'])

