from django.contrib import admin

from gallery.models import Gallery, Photo, GalleryMultiupload


class PhotoInline(admin.StackedInline):

    model = Photo


class GalleryAdmin(admin.ModelAdmin):

    inlines = [PhotoInline, ]

admin.site.register(Photo)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(GalleryMultiupload)
