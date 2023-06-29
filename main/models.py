from django.contrib.auth.models import User
from django.db import models
from django.db.models import Model

# Create your models here.

class Event(Model):
    name = models.CharField(max_length=1000)
    description = models.TextField()
    creators = models.ManyToManyField(User, related_name='creator_events')
    users = models.ManyToManyField(User, related_name='shared_events', blank=True)

    def __str__(self):
        return self.name


class SubEvents(Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    order = models.IntegerField(editable=True)
    users = models.ManyToManyField(User, related_name='accessible_subevents', blank=True)

    def __str__(self):
        return self.name


class Files(Model):
    sub_events = models.ForeignKey(SubEvents, on_delete=models.CASCADE)
    file = models.FileField(upload_to="file_uploads/")
    order = models.IntegerField(editable=True)

    def __str__(self) -> str:
        return self.sub_events.name
    

class InvitedPerson(Model):
    email = models.EmailField()
    event_id = models.IntegerField()
    creator = models.BooleanField()
    subevents = models.CharField(max_length=1000)

    def __str__(self) -> str:
        return self.email
