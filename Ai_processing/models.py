from django.db import models

# Create your models here.

class Ai_feature(models.Model):
    name = models.CharField(max_length=100, choices=[
        ('SUPER_RESOLUTION', 'Super Resolution'),
        ('COLORIZATION', 'Colorization'),
        ('DE_NOISE', 'Denoise'),
        ('DE_BLUR', 'Deblur'),
    ])
    
    description = models.TextField(blank=True, null=True)

    
    def __str__(self):
        return self.name