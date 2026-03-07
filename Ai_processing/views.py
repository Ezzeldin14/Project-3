import base64
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

    Returns the processed image as base64 + saves to user history.
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
            # Convert to RGB if necessary (e.g. RGBA PNGs, palette mode)
            if pil_image.mode not in ('RGB', 'L'):
                pil_image = pil_image.convert('RGB')
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

        # --- Encode processed image to base64 for the response ---
        processed_buffer.seek(0)
        b64_image = base64.b64encode(processed_buffer.read()).decode('utf-8')

        return Response({
            "message": "Image processed successfully",
            "feature_used": feature,
            "original_image": history.image_uploaded.url,
            "processed_image": history.restored_image.url,
            "processed_image_base64": f"data:image/png;base64,{b64_image}",
            "history_id": history.id,
        }, status=status.HTTP_200_OK)
