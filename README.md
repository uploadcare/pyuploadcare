# How to use it with Django?

    from django.db import models

    from pyuploadcare.dj import FileField

    # Create your models here.
    class Photo(models.Model):
        title = models.CharField(max_length=255)
        photo = FileField()

![Admin page](http://f.cl.ly/items/1v120O3h2W462o3T323F/Screen%20Shot%202011-11-04%20at%202.03.32%20PM.png)

See `test_project/gallery/` for an example.