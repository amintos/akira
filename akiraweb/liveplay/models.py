from django.db import models

# Create your models here.

class Game(models.Model):

    name = models.CharField(max_length=1000)
    code = models.TextField()

class Match(models.Model):

    game = models.ForeignKey("Game")
    goal = models.IntegerField()


