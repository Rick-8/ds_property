from django.contrib import admin
from .models import ServicePackage, ServiceAgreement


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_category_display', 'get_tier_display', 'price_usd', 'is_active']
    list_filter = ['category', 'tier', 'is_active']
    search_fields = ['name', 'category', 'tier']

    def get_category_display(self, obj):
        return obj.get_category_display()
    get_category_display.short_description = 'Category'

    def get_tier_display(self, obj):
        return obj.get_tier_display()
    get_tier_display.short_description = 'Tier'


@admin.register(ServiceAgreement)
class ServiceAgreementAdmin(admin.ModelAdmin):
    list_display = ['user', 'service_package', 'property', 'active', 'status', 'start_date', 'end_date', 'date_created']
    list_filter = ['active', 'status', 'start_date', 'end_date']
    search_fields = ['user__username', 'service_package__name', 'property__label', 'stripe_subscription_id']
    ordering = ['-date_created']
