import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user_history.models import User_History

from .serializers import ImageProcessSerializer
from .utils import process_image


class ProcessImageView(APIView):
    """
    POST /api/processing/process/

    Accepts a multipart/form-data request with:
      - image: the uploaded image file
      - feature: one of SUPER_RESOLUTION, BASIC_FILTER, DE_NOISE, DE_BLUR, SHADOW_REMOVAL

    Returns URLs for the original and processed images + saves to user history.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
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

        # Reset file pointer and save original
        uploaded_image.seek(0)
        original_content = ContentFile(uploaded_image.read(), name=original_name)

        # --- Save the processed image as a Django file ---
        processed_buffer = BytesIO()
        processed_pil.save(processed_buffer, format='PNG')
        processed_buffer.seek(0)

        processed_name = f"processed_{unique_id}.png"
        processed_content = ContentFile(processed_buffer.read(), name=processed_name)

        # --- Create User_History record ---
        history = User_History.objects.create(
            user=request.user,
            image_uploaded=original_content,
            restored_image=processed_content,
            feature_used=feature,
        )

        # --- Build full absolute URLs for the images ---
        orig_url = history.image_uploaded.url
        proc_url = history.restored_image.url
        original_url = orig_url if orig_url.startswith('http') else request.build_absolute_uri(orig_url)
        processed_url = proc_url if proc_url.startswith('http') else request.build_absolute_uri(proc_url)

        return Response({
            "message": "Image processed successfully",
            "feature_used": feature,
            "original_image": original_url,
            "processed_image": processed_url,
            "history_id": history.id,
        }, status=status.HTTP_200_OK)
