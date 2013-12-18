from django.db import models

# Create your models here.
class Disease(models.Model):
    concept = models.CharField(max_length=100)
    synonyms = models.CharField(max_length=4000)