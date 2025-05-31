from django.contrib import admin
from .models import Route, Job, JobPhoto


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('staff',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'route', 'scheduled_date', 'status')
    list_filter = ('status', 'route', 'scheduled_date')
    search_fields = ('title', 'property__label')
    filter_horizontal = ('assigned_staff',)


@admin.register(JobPhoto)
class JobPhotoAdmin(admin.ModelAdmin):
    list_display = ('job', 'uploaded_by', 'uploaded_at')
    search_fields = ('job__title', 'uploaded_by__username')
