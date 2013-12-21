from django.db import models

# Create your models here.
class Disease(models.Model):
    concept = models.CharField(max_length=100)
    synonyms = models.CharField(max_length=4000)

class SubmatrixData(models.Model):
    term = models.CharField(max_length=100)
    method = models.CharField(max_length=20)
    nodes = models.PositiveSmallIntegerField()
    dataFilePath = models.CharField(max_length=300)