
<table>
    <tr style="border: none;">
        <td style="border: none;">
            <img src="https://ucarecdn.com/2f4864b7-ed0e-4411-965b-8148623aa680/-/inline/yes/uploadcare-logo-mark.svg" target="" width="64" height="64">
        </td>
        <th style="vertical-align: center; border: none;">
            <h1>PyUploadcare: a Python library for Uploadcare</h1>
        </th>
    </tr>
</table>

<p>
  <a href="https://pypi.org/project/pyuploadcare/">
    <img src="https://badge.fury.io/py/pyuploadcare.svg" height="25" />
  </a>
  <a href="https://github.com/uploadcare/pyuploadcare/actions?query=branch%3Amain+workflow%3ATests++">
    <img src="https://github.com/uploadcare/pyuploadcare/actions/workflows/test.yml/badge.svg" height="25" />
  </a>
  <a href="https://pyuploadcare.readthedocs.io/">
    <img src="https://readthedocs.org/projects/pyuploadcare/badge/?version=latest" height="25" />
  </a>
  <a href="https://stackshare.io/uploadcare">
    <img src="https://img.shields.io/badge/tech-stack-0690fa.svg?style=flat" height="25" />
  </a>
</p>

Uploadcare Python & Django integrations handle uploads and further operations
with files by wrapping Upload and REST APIs.

Simple file uploads for the web are of most importance for us. Today, everyone
is used to the routine of allowing users to upload their pics or attach resumes.
The routine covers it all: installing image processing libraries, adjusting
permissions, ensuring servers never go down, and enabling CDN.

This library consists of the Uploadcare API interface and a couple of Django
goodies.

Simple as that, Uploadcare `ImageField` can be added to an
existing Django project in just a couple of [simple steps](https://pyuploadcare.readthedocs.org/en/latest/quickstart.html).
This will enable your users to see the upload progress, pick files
from Google Drive or Instagram, and edit a form while files are
being uploaded asynchronously.

You can find an example project [here](https://github.com/uploadcare/pyuploadcare-example).

```python

    from django import forms
    from django.db import models

    from pyuploadcare.dj.models import ImageField
    from pyuploadcare.dj.forms import FileWidget, ImageField as ImageFormField


    class Candidate(models.Model):
        photo = ImageField(blank=True, manual_crop="")


    # optional. provide advanced widget options: https://uploadcare.com/docs/uploads/widget/config/#options
    class CandidateForm(forms.Form):
        photo = ImageFormField(widget=FileWidget(attrs={
            'data-cdn-base': 'https://cdn.super-candidates.com',
            'data-image-shrink': '1024x1024',
        }))

```

![](https://ucarecdn.com/dbb4021e-b20e-40fa-907b-3da0a4f8ed70/-/resize/800/manual_crop.png)

## Documentation

Detailed documentation is available [on RTD](https://pyuploadcare.readthedocs.io/en/latest/).

## Feedback

Issues and PRs are welcome. You can provide your feedback or drop us a support
request at [hello@uploadcare.com](hello@uploadcare.com).
