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
            # Use RawMediaCloudinaryStorage to prevent quality degradation
            import os as _os
            if _os.getenv("CLOUDINARY_URL"):
                from cloudinary_storage.storage import RawMediaCloudinaryStorage
                storage = RawMediaCloudinaryStorage()
            else:
                from django.core.files.storage import default_storage
                storage = default_storage

            original_path = storage.save(
                f"user_history/{original_name}", original_content
            )
            processed_path = storage.save(
                f"user_history/restored/{processed_name}", processed_content
            )

            original_url = storage.url(original_path)
            processed_url = storage.url(processed_path)

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

    Processes an image and saves both original and processed versions
    to the user's history.
    Called by the Flutter app when the user clicks "Save".

    Accepts multipart/form-data with:
      - image: the uploaded image file
      - feature: one of SUPER_RESOLUTION, COLORIZATION, DE_BLUR, etc.
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
            from .utils import process_image

            serializer = SaveToHistorySerializer(data=request.data)
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

            # Save the original uploaded image
            unique_id = uuid.uuid4().hex[:12]
            uploaded_image.seek(0)
            original_content = ContentFile(
                uploaded_image.read(),
                name=f"original_{unique_id}.png"
            )

            # Save the processed image
            processed_buffer = BytesIO()
            processed_pil.save(processed_buffer, format='PNG')
            processed_buffer.seek(0)
            processed_content = ContentFile(
                processed_buffer.read(),
                name=f"processed_{unique_id}.png"
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
