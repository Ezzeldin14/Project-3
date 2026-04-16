import logging
import traceback
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer

logger = logging.getLogger(__name__)

from user_history.models import User_History

from .serializers import ImageProcessSerializer, SaveToHistorySerializer


class DebugPingView(APIView):
    """Temporary debug endpoint — returns JSON to verify deployment is live."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok", "version": "deblur-fix-v3"})


class ProcessImageView(APIView):
    """
    POST /api/processing/process/

    Accepts a multipart/form-data request with:
      - image: the uploaded image file
      - feature: one of SUPER_RESOLUTION, COLORIZATION, DE_BLUR, etc.

    Processes the image and returns URLs for both original and processed images.
    Does NOT save to history — use /api/processing/save/ for that.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ImageProcessSerializer,
        responses={200: inline_serializer('ProcessImageResponse', fields={
            'message': drf_serializers.CharField(),
            'feature_used': drf_serializers.CharField(),
            'original_image': drf_serializers.URLField(),
            'processed_image': drf_serializers.URLField(),
        })},
    )
    def post(self, request):
        try:
            from .utils import process_image

            serializer = ImageProcessSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            uploaded_image = serializer.validated_data['image']
            feature = serializer.validated_data['feature']

            # Open the uploaded image with Pillow
            try:
                pil_image = Image.open(uploaded_image)
            except Exception:
                return Response(
                    {"error": "Invalid image file. Could not open the image."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process the image
            try:
                processed_pil = process_image(pil_image, feature)
            except ValueError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # --- Save the original uploaded image as a Django file ---
            unique_id = uuid.uuid4().hex[:12]
            original_name = f"original_{unique_id}.png"

            uploaded_image.seek(0)
            original_content = ContentFile(uploaded_image.read(), name=original_name)

            # --- Save the processed image as a Django file ---
            processed_buffer = BytesIO()
            processed_pil.save(processed_buffer, format='PNG')
            processed_buffer.seek(0)

            processed_name = f"processed_{unique_id}.png"
            processed_content = ContentFile(processed_buffer.read(), name=processed_name)

            # Upload images to storage (Cloudinary) without creating history
            # We use a temporary model instance just to get the URLs
            from django.core.files.storage import default_storage

            original_path = default_storage.save(
                f"user_history/{original_name}", original_content
            )
            processed_path = default_storage.save(
                f"user_history/restored/{processed_name}", processed_content
            )

            original_url = default_storage.url(original_path)
            processed_url = default_storage.url(processed_path)

            # Make URLs absolute if they're relative
            if not original_url.startswith('http'):
                original_url = request.build_absolute_uri(original_url)
            if not processed_url.startswith('http'):
                processed_url = request.build_absolute_uri(processed_url)

            return Response({
                "message": "Image processed successfully",
                "feature_used": feature,
                "original_image": original_url,
                "processed_image": processed_url,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            tb = traceback.format_exc()
            logger.exception("Unhandled error in ProcessImageView: %s", e)
            return Response(
                {"error": f"Processing failed: {str(e)}", "traceback": tb},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SaveToHistoryView(APIView):
    """
    POST /api/processing/save/

    Saves a processed image to the user's history.
    Called by the Flutter app when the user clicks "Save".

    Accepts JSON with:
      - original_image: URL of the original image (from /process/ response)
      - processed_image: URL of the processed image (from /process/ response)
      - feature: the feature that was used
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SaveToHistorySerializer,
        responses={201: inline_serializer('SaveToHistoryResponse', fields={
            'message': drf_serializers.CharField(),
            'history_id': drf_serializers.IntegerField(),
        })},
    )
    def post(self, request):
        try:
            serializer = SaveToHistorySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            original_url = serializer.validated_data['original_image']
            processed_url = serializer.validated_data['processed_image']
            feature = serializer.validated_data['feature']

            # Download images from URLs and save to history
            import requests as http_requests

            # Download original image
            orig_response = http_requests.get(original_url, timeout=30)
            orig_response.raise_for_status()
            original_content = ContentFile(
                orig_response.content,
                name=f"original_{uuid.uuid4().hex[:12]}.png"
            )

            # Download processed image
            proc_response = http_requests.get(processed_url, timeout=30)
            proc_response.raise_for_status()
            processed_content = ContentFile(
                proc_response.content,
                name=f"processed_{uuid.uuid4().hex[:12]}.png"
            )

            # Create history entry
            history = User_History.objects.create(
                user=request.user,
                image_uploaded=original_content,
                restored_image=processed_content,
                feature_used=feature,
            )

            return Response({
                "message": "Image saved to history",
                "history_id": history.id,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            tb = traceback.format_exc()
            logger.exception("Unhandled error in SaveToHistoryView: %s", e)
            return Response(
                {"error": f"Save failed: {str(e)}", "traceback": tb},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
