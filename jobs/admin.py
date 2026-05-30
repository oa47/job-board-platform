from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'location', 'job_type', 'created_at')
    list_filter = ('job_type', 'created_at', 'location')
    search_fields = ('title', 'description', 'employer__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'employer', 'description')
        }),
        ('Details', {
            'fields': ('location', 'job_type', 'salary_min', 'salary_max')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
