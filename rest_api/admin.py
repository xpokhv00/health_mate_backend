from django.contrib import admin

from .models import Message, Medication, Treatment, Diagnosis, Profile, Appointment

# Register your models here.

admin.site.register(Message)
admin.site.register(Medication)
admin.site.register(Treatment)
admin.site.register(Diagnosis)
admin.site.register(Profile)
admin.site.register(Appointment)
