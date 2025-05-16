from django.contrib import admin
from .models import Profile, Property


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'account_status', 'is_verified')
    list_filter = ('user_type', 'account_status', 'is_verified')
    readonly_fields = ('date_created',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('label', 'profile', 'city', 'postcode', 'is_active')
    list_filter = ('is_active', 'country')
    search_fields = ('label', 'city', 'postcode')
