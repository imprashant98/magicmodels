from django.db import models

class User(models.Model):
    username = models.CharField(max_length=255, db_index=True)
    email = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posts = models.ManyToManyField('post.Post')

    def __str__(self):
        return str(self.pk)

