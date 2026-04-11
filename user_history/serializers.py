from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

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

    def _absolute_url(self, field, request):
        """Return full URL for an image field, handling both Cloudinary and local storage."""
        if not field:
            return None
        url = field.url
        # Cloudinary already returns an absolute https:// URL
        if url.startswith('http'):
            return url
        # Local storage — build absolute URI from the request
        if request:
            return request.build_absolute_uri(url)
        return url

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_image_uploaded(self, obj):
        return self._absolute_url(obj.image_uploaded, self.context.get('request'))

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_restored_image(self, obj):
        return self._absolute_url(obj.restored_image, self.context.get('request'))
