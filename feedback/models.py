from django.db import models

class Feedback(models.Model):
    POSITIVE = 'Positive'
    NEGATIVE = 'Negative'
    FEEDBACK_CHOICES = [
        (POSITIVE, 'Positive'),
        (NEGATIVE, 'Negative'),
    ]

    feedback_text = models.TextField() 
    feedback_type = models.CharField(
        max_length=8,
        choices=FEEDBACK_CHOICES,
        default=POSITIVE,
    )
    feedback_time = models.DateTimeField(auto_now_add=True)  
    sector = models.CharField(
        max_length=100,  
        blank=True,      
        null=True,       
    )

    def __str__(self):
        return f"Feedback from {self.feedback_time} - {self.feedback_type} - {self.sector}"


