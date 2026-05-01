from rest_framework import serializers

FEATURE_CHOICES = [
    ('SUPER_RESOLUTION', 'Super Resolution'),
    ('COLORIZATION', 'Colorization'),
    ('DE_BLUR', 'Deblur'),
    ('BILATERAL_FILTER', 'Bilateral Filter'),
    ('GAUSSIAN_FILTER', 'Gaussian Filter'),
    ('GUIDED_FILTER', 'Guided Filter'),
    ('MEDIAN_FILTER', 'Median Filter'),
]


class ImageProcessSerializer(serializers.Serializer):
    image = serializers.ImageField()
    feature = serializers.ChoiceField(choices=FEATURE_CHOICES)


class SaveToHistorySerializer(serializers.Serializer):
    processed_image = serializers.URLField()
    feature = serializers.ChoiceField(choices=FEATURE_CHOICES)
