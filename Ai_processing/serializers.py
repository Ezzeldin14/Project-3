from rest_framework import serializers

FEATURE_CHOICES = [
    ('SUPER_RESOLUTION', 'Super Resolution'),
    ('BASIC_FILTER', 'Basic Filter'),
    ('DE_NOISE', 'Denoise'),
    ('DE_BLUR', 'Deblur'),
    ('SHADOW_REMOVAL', 'Shadow Removal'),
]


class ImageProcessSerializer(serializers.Serializer):
    image = serializers.ImageField()
    feature = serializers.ChoiceField(choices=FEATURE_CHOICES)
