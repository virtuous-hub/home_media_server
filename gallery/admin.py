from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'must_change_password',
        'can_manage_private',
    )

    list_filter = (
        'must_change_password',
        'can_manage_private',
    )

    search_fields = (
        'user__username',
    )