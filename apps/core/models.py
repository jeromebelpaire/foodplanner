from django.db import models
from django.conf import settings


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
