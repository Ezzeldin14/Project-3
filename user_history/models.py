import os

from django.db import models
from users.models import User

# Use RawMediaCloudinaryStorage to prevent Cloudinary from applying
# automatic compression / format conversion that degrades image quality.
if os.getenv("CLOUDINARY_URL"):
    from cloudinary_storage.storage import RawMediaCloudinaryStorage
    _media_storage = RawMediaCloudinaryStorage()
else:
    _media_storage = None  # use Django default (local filesystem)


# Create your models here.
class User_History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    image_uploaded = models.ImageField(upload_to='user_history/', storage=_media_storage, blank=True, null=True)
    restored_image = models.ImageField(upload_to='user_history/restored/', storage=_media_storage)
    feature_used = models.CharField(
        max_length=50,
        choices=[
            ('SUPER_RESOLUTION', 'Super Resolution'),
            ('COLORIZATION', 'Colorization'),
            ('DE_BLUR', 'Deblur'),
            ('BILATERAL_FILTER', 'Bilateral Filter'),
            ('GAUSSIAN_FILTER', 'Gaussian Filter'),
            ('GUIDED_FILTER', 'Guided Filter'),
            ('MEDIAN_FILTER', 'Median Filter'),
        ],
        default='DE_BLUR',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"History of {self.user.email} at {self.created_at}"