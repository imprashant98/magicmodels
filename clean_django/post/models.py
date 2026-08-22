from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    author = models.ForeignKey('user.User', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pk)
