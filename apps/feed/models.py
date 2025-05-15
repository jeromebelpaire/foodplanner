from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.recipes.models import Recipe, RecipeRating


class FeedItem(models.Model):
    class EventType(models.TextChoices):
        NEW_RECIPE = "new_recipe", _("New Recipe")
        NEW_RATING = "new_rating", _("New Rating")
        UPDATE_RECIPE = "update_recipe", _("Update Recipe")
        UPDATE_RATING = "update_rating", _("Update Rating")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feed_items")
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )
    created_on = models.DateTimeField(auto_now_add=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.ForeignKey(RecipeRating, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()} - {self.created_on.strftime('%Y-%m-%d')}"


class FeedItemLike(models.Model):
    """Represents a user liking a specific feed item."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feed_likes")
    feed_item = models.ForeignKey(FeedItem, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "feed_item")
        ordering = ["-created_at"]
        verbose_name = "Feed Item Like"
        verbose_name_plural = "Feed Item Likes"

    def __str__(self):
        user_repr = getattr(self.user, "username", f"User {self.user_id}")
        return f"{user_repr} likes FeedItem {self.feed_item_id}"


class FeedItemComment(models.Model):
    """Represents a comment made by a user on a specific feed item."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feed_comments")
    feed_item = models.ForeignKey(FeedItem, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Feed Item Comment"
        verbose_name_plural = "Feed Item Comments"

    def __str__(self):
        user_repr = getattr(self.user, "username", f"User {self.user_id}")
        return f"Comment by {user_repr} on FeedItem {self.feed_item_id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
