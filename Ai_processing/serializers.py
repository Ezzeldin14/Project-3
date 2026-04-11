from rest_framework import serializers

FEATURE_CHOICES = [
    ('SUPER_RESOLUTION', 'Super Resolution'),
    ('COLORIZATION', 'Colorization'),
    ('DE_NOISE', 'Denoise'),
    ('DE_BLUR', 'Deblur'),
]


class ImageProcessSerializer(serializers.Serializer):
    image = serializers.ImageField()
    feature = serializers.ChoiceField(choices=FEATURE_CHOICES)
