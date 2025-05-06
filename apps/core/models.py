from django.db import models
from django.conf import settings
from django.utils import timezone


class Follow(models.Model):
    """
    Represents a follow relationship between two users.
    'follower' is the user initiating the follow.
    'followed' is the user being followed.
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="following_set",  # user.following_set.all() gives Follow objects where user is follower
        on_delete=models.CASCADE,
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="followers_set",  # user.followers_set.all() gives Follow objects where user is followed
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a user cannot follow the same person multiple times
        unique_together = ("follower", "followed")
        ordering = ["-created_at"]
        verbose_name = "Follow Relationship"
        verbose_name_plural = "Follow Relationships"

    def __str__(self):
        # Use username if available, otherwise fallback to ID
        follower_repr = getattr(self.follower, "username", f"User {self.follower_id}")
        followed_repr = getattr(self.followed, "username", f"User {self.followed_id}")
        return f"{follower_repr} follows {followed_repr}"


class TermsOfServiceVersion(models.Model):
    """Stores different versions of the Terms of Service."""

    version_number = models.CharField(max_length=20, unique=True, help_text="e.g., '1.0', '2024-07-15'")
    content = models.TextField(help_text="The full text of the Terms of Service for this version.")
    published_at = models.DateTimeField(default=timezone.now, help_text="When this version becomes active.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]  # Default ordering shows latest published first
        verbose_name = "Terms of Service Version"
        verbose_name_plural = "Terms of Service Versions"

    def __str__(self):
        return f"ToS Version {self.version_number} (Published: {self.published_at.strftime('%Y-%m-%d')})"


class UserProfile(models.Model):
    """Extends the built-in User model with additional profile information."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    tos_accepted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the user accepted the ToS.")
    accepted_tos_version = models.ForeignKey(
        TermsOfServiceVersion,
        on_delete=models.SET_NULL,  # Keep profile even if ToS version is deleted (consider implications)
        null=True,
        blank=True,
        related_name="accepted_by_profiles",
        help_text="The specific version of ToS accepted by the user.",
    )

    # Add other profile fields here if needed in the future (e.g., avatar, bio)

    def __str__(self):
        username = getattr(self.user, "username", f"User {self.user_id}")
        return f"Profile for {username}"
