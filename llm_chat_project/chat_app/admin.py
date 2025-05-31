from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Pessoa

admin.site.register(Pessoa)
