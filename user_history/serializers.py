from rest_framework import serializers

from .models import User_History


class UserHistorySerializer(serializers.ModelSerializer):
    image_uploaded = serializers.ImageField(read_only=True)
    restored_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User_History
        fields = (
            'id',
            'image_uploaded',
            'restored_image',
            'feature_used',
            'created_at',
        )
        read_only_fields = fields
