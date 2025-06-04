from django.contrib import admin
from .models import Profile, Property


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Profile._meta.fields]
    list_filter = ('user_type', 'account_status', 'profile_completed')
    search_fields = ('user__username', 'email', 'phone', 'company_name')
    readonly_fields = ('date_created',)
    ordering = ('-date_created',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Property._meta.fields]
    list_filter = ('is_active', 'has_active_service', 'country')
    search_fields = ('label', 'address_line_1', 'city', 'postcode')
    readonly_fields = ('date_added',)
    ordering = ('-date_added',)
