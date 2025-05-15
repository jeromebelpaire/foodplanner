from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import TermsOfServiceVersion, UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    # Fields to display/edit in the inline form
    fields = ("tos_accepted_at", "accepted_tos_version")
    readonly_fields = ("tos_accepted_at",)


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "get_tos_accepted_version")
    list_select_related = ("profile", "profile__accepted_tos_version")

    def get_tos_accepted_version(self, instance):
        try:
            if instance.profile and instance.profile.accepted_tos_version:
                return instance.profile.accepted_tos_version.version_number
        except UserProfile.DoesNotExist:
            pass
        return "N/A"

    get_tos_accepted_version.short_description = "ToS Version Accepted"

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(TermsOfServiceVersion)
class TermsOfServiceVersionAdmin(admin.ModelAdmin):
    list_display = ("version_number", "published_at", "created_at")
    search_fields = ("version_number", "content")
    list_filter = ("published_at",)
    ordering = ("-published_at",)
    fields = ("version_number", "published_at", "content")


# Re-register UserAdmin (unregister the default first)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
