from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


class CustomUser(AbstractUser):

    ROLE_CHOICES = [
        ('player',    'Player'),
        ('organizer', 'Organizer'),
        ('admin',     'Admin'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='player',
    )

    address = models.CharField(max_length=255, blank=True)
    phone   = models.CharField(max_length=20,  blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class PlatformBranding(models.Model):
    """Single admin-managed set of public visual assets, stored on Cloudinary."""
    logo = CloudinaryField('organization_logo', blank=True, null=True)
    landing_video = CloudinaryField('landing_background_video', resource_type='video', blank=True, null=True)
    login_background = CloudinaryField('login_background', blank=True, null=True)
    register_background = CloudinaryField('register_background', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    DEFAULT_LOGO = 'https://res.cloudinary.com/i4p3gnjs/image/upload/v1786217841/marksmen_logo_a4oubo.png'
    DEFAULT_LANDING_VIDEO = 'https://res.cloudinary.com/i4p3gnjs/video/upload/v1786217855/home_video_ozsslq.webm'
    DEFAULT_AUTH_BACKGROUND = 'https://res.cloudinary.com/i4p3gnjs/image/upload/v1786217839/cse412_agknup.jpg'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def _url(self, field_name, fallback):
        asset = getattr(self, field_name)
        return asset.url if asset else fallback

    @property
    def logo_url(self):
        return self._url('logo', self.DEFAULT_LOGO)

    @property
    def landing_video_url(self):
        return self._url('landing_video', self.DEFAULT_LANDING_VIDEO)

    @property
    def login_background_url(self):
        return self._url('login_background', self.DEFAULT_AUTH_BACKGROUND)

    @property
    def register_background_url(self):
        return self._url('register_background', self.DEFAULT_AUTH_BACKGROUND)


class PlayerProfile(models.Model):
    """
    Extra profile info specific to players.
    One-to-one with CustomUser — one profile per player.
    """

    INGAME_ROLE_CHOICES = [
    ('',            'Prefer not to say'),
    ('assault',     'Assault'),
    ('skirmisher',  'Skirmisher'),
    ('support',     'Support'),
    ('controller',  'Controller'),
    ('recon',       'Recon'),
]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='player_profile',
    )

    # in-game role the player prefers
    ingame_role = models.CharField(
        max_length=20,
        choices=INGAME_ROLE_CHOICES,
        blank=True,
    )

    # optional short bio
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.ingame_role}"
