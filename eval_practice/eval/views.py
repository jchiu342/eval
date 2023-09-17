import random
import os

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Eval

GO4GO_PATH = '/mnt/c/Users/wtasf/OneDrive/Documents/go/projects/go4go_db'

def eval(request):
  template = loader.get_template('first.html')
  context = {
    'asdf': random.choice(Eval.objects.all().values())
  }
  return HttpResponse(template.render(context, request))