from django.db import models

class FAQ(models.Model):
    question = models.TextField(unique=True)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.question

