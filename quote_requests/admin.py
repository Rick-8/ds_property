from django.contrib import admin
from .models import QuoteRequest


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('name', 'email', 'description')
