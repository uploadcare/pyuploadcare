from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
import json
import time
import hashlib
import hmac
from .forms import ImgForm
from pyuploadcare import FileGroup, generate_secure_signature
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


def index(request):
    imgForm = ImgForm()
    return render(request, 'sampleapp/index.html', {'form': imgForm})


@csrf_exempt
def release_signature(request):
    # we will set the signature to expire in 30 min
    expire = int(time.time()) + 60 * 30
    signature = generate_secure_signature(
                settings.UPLOADCARE['secret'],
                expire)
    return HttpResponse(json.dumps({'signature': signature, 'expire': expire}), content_type="application/json")
