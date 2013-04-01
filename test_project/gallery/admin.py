from django.contrib import admin

from gallery.models import Gallery, Photo


class PhotoInline(admin.StackedInline):

    model = Photo


class GalleryAdmin(admin.ModelAdmin):

    inlines = [PhotoInline, ]

admin.site.register(Photo)
admin.site.register(Gallery, GalleryAdmin)
