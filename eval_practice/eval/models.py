from django.db import models

class Eval(models.Model):
  name = models.CharField(max_length=255)
  sgf_content = models.CharField(max_length=1023)
  move = models.IntegerField()
  score = models.FloatField()
