from django.db import models


class Comment(models.Model):
    body = models.TextField()
    post = models.ForeignKey('post.Post', on_delete=models.CASCADE)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pk)
