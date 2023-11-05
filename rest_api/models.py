from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from rest_framework import generics

from users.models import CustomUser


# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, null=True, on_delete=models.CASCADE)
    age = models.IntegerField(
        validators=[
            MaxValueValidator(limit_value=120)
        ]
    )
    gender = models.CharField(max_length=64)
    height = models.IntegerField(
        validators=[
            MaxValueValidator(limit_value=300)
        ]
    )
    weight = models.IntegerField(
        validators=[
            MaxValueValidator(limit_value=200)
        ]
    )
    name = models.CharField(max_length=128)
    profession = models.CharField(max_length=128, default="Paediatrician")
    preconditions = models.TextField()
    address = models.CharField(max_length=255)
    allergies = models.TextField()


class Message(models.Model):
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="message_patient")
    doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="message_doctor")
    message = models.TextField()


class Treatment(models.Model):
    times = models.TextField(default='')
    patient = models.ForeignKey(CustomUser, related_name="treatment_patient", on_delete=models.CASCADE)
    doctor = models.ForeignKey(CustomUser, related_name="treatment_doctor", on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default='')
    duration = models.IntegerField(default=7,
                                   validators=[
                                       MaxValueValidator(limit_value=100)
                                   ]
                                   )
    dosage = models.IntegerField(
        validators=[
            MaxValueValidator(limit_value=1000)
        ]
    )
    finish_date = models.DateTimeField(default=(timezone.now() + timezone.timedelta(days=7)))
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Calculate the finish date based on the created_at and duration
        self.finish_date = self.created_at + timezone.timedelta(days=self.duration)
        super(Treatment, self).save(*args, **kwargs)


class Medication(models.Model):
    name = models.CharField(max_length=256)
    use_case = models.CharField(max_length=256)
    how_to_use = models.CharField(max_length=256)
    side_effects = models.CharField(max_length=256)

class Appointment(models.Model):
    title = models.CharField(max_length=256)
    date = models.DateField()
    timeFrom = models.TimeField()
    timeTo = models.TimeField()
    patient = models.ForeignKey(CustomUser, default=1, related_name="appointment_patient", on_delete=models.CASCADE)
    doctor = models.ForeignKey(CustomUser, default=1, related_name="appointment_doctor", on_delete=models.CASCADE)

class Diagnosis(models.Model):
    name = models.CharField(max_length=256)
    next_steps = models.TextField()
    notes = models.TextField()
    patient = models.ForeignKey(CustomUser, default=1, related_name="diagnosis_patient", on_delete=models.CASCADE)
    doctor = models.ForeignKey(CustomUser, default=1, related_name="diagnosis_doctor", on_delete=models.CASCADE)
