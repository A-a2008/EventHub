from django.contrib import admin
from .models import Event, SubEvents, Files

# Register your models here.


class SubEventsInline(admin.StackedInline):
    model = SubEvents
    extra = 0


class EventsAdmin(admin.ModelAdmin):
    inlines = [SubEventsInline]


class FilesInline(admin.StackedInline):
    model = Files
    extra = 0


class SubEventsAdmin(admin.ModelAdmin):
    inlines = [FilesInline]

admin.site.register(Event, EventsAdmin)
admin.site.register(SubEvents, SubEventsAdmin)


admin.site.site_title = "EventHub"
admin.site.site_header = "EventHub Administration"
admin.site.index_title = "EventHub Administration"
