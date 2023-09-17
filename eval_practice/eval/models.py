from django.db import models

class Eval(models.Model):
  name = models.CharField(max_length=255)
  move = models.IntegerField()
  score = models.FloatField()
