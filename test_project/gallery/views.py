# coding: utf-8
from django.core.urlresolvers import reverse
from django.views.generic import CreateView, DetailView

from .forms import MyForm
from .models import LocalPhoto
from gallery.tasks import download_photo


class CeleryDownloadView(CreateView):

    form_class = MyForm
    template_name = 'gallery/form.html'

    def form_valid(self, form):
        local_photo = form.save()
        download_photo.delay(local_photo.pk, form.cleaned_data['uc_uuid'])

        return reverse('celery_result', kwargs={'pk': local_photo.pk})


class CeleryResultView(DetailView):

    template_name = 'gallery/result.html'
    model = LocalPhoto
