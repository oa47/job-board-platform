from django.contrib import admin
from .models import Application, ApplicationStatus


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at', 'job')
    search_fields = ('candidate__username', 'job__title')
    readonly_fields = ('applied_at', 'reviewed_at')
    actions = ['mark_reviewed', 'mark_accepted', 'mark_rejected']

    def mark_reviewed(self, request, queryset):
        queryset.update(status=ApplicationStatus.REVIEWED)
    mark_reviewed.short_description = "Mark selected as Reviewed"

    def mark_accepted(self, request, queryset):
        queryset.update(status=ApplicationStatus.ACCEPTED)
    mark_accepted.short_description = "Mark selected as Accepted"

    def mark_rejected(self, request, queryset):
        queryset.update(status=ApplicationStatus.REJECTED)
    mark_rejected.short_description = "Mark selected as Rejected"
