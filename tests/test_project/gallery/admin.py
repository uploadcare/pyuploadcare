from django.contrib import admin

from .models import Gallery, GalleryMultiupload, Photo


class PhotoInline(admin.StackedInline):

    model = Photo


class GalleryAdmin(admin.ModelAdmin):

    inlines = [
        PhotoInline,
    ]


admin.site.register(Photo)
admin.site.register(Gallery, GalleryAdmin)
admin.site.register(GalleryMultiupload)
