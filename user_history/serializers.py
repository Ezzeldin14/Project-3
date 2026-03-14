from rest_framework import serializers

from .models import User_History


class UserHistorySerializer(serializers.ModelSerializer):
    image_uploaded = serializers.SerializerMethodField()
    restored_image = serializers.SerializerMethodField()

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

    def get_image_uploaded(self, obj):
        request = self.context.get('request')
        if obj.image_uploaded and request:
            return request.build_absolute_uri(obj.image_uploaded.url)
        return None

    def get_restored_image(self, obj):
        request = self.context.get('request')
        if obj.restored_image and request:
            return request.build_absolute_uri(obj.restored_image.url)
        return None
