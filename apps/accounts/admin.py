from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from apps.accounts.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "is_staff",'last_login','date_joined')
    list_display_links = ("id", "username", )
    readonly_fields = ("date_joined", "last_login")
    filter_horizontal = ("groups", "user_permissions")
    search_fields = ("username", "email")
    ordering = ("username",)


    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "middle_name",
                    "avatar",
                    "phone_number",
                    "role",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    'avatar',
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )
