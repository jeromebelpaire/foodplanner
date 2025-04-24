from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.recipes.models import Recipe, RecipeRating


class FeedItem(models.Model):
    class EventType(models.TextChoices):
        NEW_RECIPE = "NR", _("New Recipe")
        NEW_RATING = "RA", _("New Rating")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feed_items")
    event_type = models.CharField(
        max_length=2,
        choices=EventType.choices,
    )
    created_on = models.DateTimeField(auto_now_add=True)
    # Null if event_type is not NEW_RECIPE
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True)
    # Null if event_type is not NEW_RATING
    rating = models.ForeignKey(RecipeRating, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()} - {self.created_on.strftime('%Y-%m-%d')}"
