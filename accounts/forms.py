
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, PlayerProfile, PlatformBranding


class RegisterForm(UserCreationForm):

    ROLE_CHOICES = [
        ('player',    'Player'),
        ('organizer', 'Organizer'),
    ]

    role    = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect, initial='player')
    email   = forms.EmailField(required=True)
    phone   = forms.CharField(max_length=20,  required=False)
    address = forms.CharField(max_length=255, required=False)

    class Meta:
        model  = CustomUser
        fields = ['username', 'email', 'phone', 'address', 'role', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already registered.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email


class LoginForm(AuthenticationForm):
    pass


class PlatformBrandingForm(forms.ModelForm):
    class Meta:
        model = PlatformBranding
        fields = ['logo', 'landing_video', 'login_background', 'register_background']
        widgets = {
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'landing_video': forms.FileInput(attrs={'accept': 'video/*'}),
            'login_background': forms.FileInput(attrs={'accept': 'image/*'}),
            'register_background': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class PlayerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50,  required=False, label='First name')
    last_name  = forms.CharField(max_length=50,  required=False, label='Last name')
    email      = forms.EmailField(required=False, label='Email')
    phone      = forms.CharField(max_length=20,  required=False, label='Phone')
    address    = forms.CharField(max_length=255, required=False, label='Address')

    class Meta:
        model  = PlayerProfile
        fields = ['ingame_role', 'bio']
        widgets = {
            'ingame_role': forms.RadioSelect(),  # ← THIS is the fix
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial  = self.user.last_name
            self.fields['email'].initial      = self.user.email
            self.fields['phone'].initial      = self.user.phone
            self.fields['address'].initial    = self.user.address

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name  = self.cleaned_data.get('last_name',  '')
            self.user.email      = self.cleaned_data.get('email',      '')
            self.user.phone      = self.cleaned_data.get('phone',      '')
            self.user.address    = self.cleaned_data.get('address',    '')
            self.user.save()
        if commit:
            profile.save()
        return profile


class OrganizerProfileForm(forms.ModelForm):
    """
    Organizer and Admin share the same profile form —
    just name, email, phone, address on CustomUser.
    """

    first_name = forms.CharField(max_length=50,  required=False, label='First name')
    last_name  = forms.CharField(max_length=50,  required=False, label='Last name')
    email      = forms.EmailField(required=False, label='Email')
    phone      = forms.CharField(max_length=20,  required=False, label='Phone')
    address    = forms.CharField(max_length=255, required=False, label='Address')




    class Meta:
        model  = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']
