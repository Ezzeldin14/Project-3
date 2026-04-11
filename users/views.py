from rest_framework import generics, serializers as drf_serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
import logging

from .models import EmailVerificationOTP, PasswordResetOTP, User
from .serializers import (
    LoginSerializer,
    RequestPasswordResetSerializer,
    SetNewPasswordSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    VerifyEmailOTPSerializer,
    GoogleLoginSerializer,
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp_code = EmailVerificationOTP.generate_otp()
        
        EmailVerificationOTP.objects.create(user=user, otp=otp_code)

        email_body = f"""
            <h2>Welcome to PixelRevive!</h2>
            <p>Your verification code is:</p>
            <h1 style="color: #4CAF50; letter-spacing: 5px; font-size: 36px;">{otp_code}</h1>
            <p>This OTP will expire in 15 minutes.</p>
            <p>If you didn't create this account, please ignore this email.</p>
            """

        email = EmailMultiAlternatives(
            subject="Verify your PixelRevive email",
            body=f"Your verification code is: {otp_code}",
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],
        )
        email.attach_alternative(email_body, "text/html")
        
        try:
            email.send()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Account created. Check your email for the verification code.",
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)







class VerifyEmailView(generics.GenericAPIView):
    serializer_class = VerifyEmailOTPSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({"message": "Email verified successfully!"})







class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        return self.request.user
    
    
    
    
    


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RequestPasswordResetSerializer,
        responses={200: inline_serializer('PasswordResetOTPSent', fields={'detail': drf_serializers.CharField()})},
    )
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        otp_code = PasswordResetOTP.generate_otp()
        
        PasswordResetOTP.objects.create(user=user, otp=otp_code)

        email_body = f"""
        <h2>Password Reset Request</h2>
        <p>Your OTP for password reset is:</p>
        <h1 style="color: #4CAF50; letter-spacing: 5px; font-size: 36px;">{otp_code}</h1>
        <p>This OTP will expire in 15 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """

        email = EmailMultiAlternatives(
            subject="Your Password Reset OTP",
            body=f"Your OTP is {otp_code}", 
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],                
        )

        email.attach_alternative(email_body, "text/html")
        
        try:
            email.send()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")

        return Response({"detail": "OTP sent to your email"})




class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SetNewPasswordSerializer,
        responses={200: inline_serializer('PasswordResetDone', fields={'detail': drf_serializers.CharField()})},
    )
    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Password has been reset successfully"})
    
    
    
    

class GoogleContinueView(APIView):

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @extend_schema(
        request=GoogleLoginSerializer,
        responses={200: inline_serializer('GoogleLoginResponse', fields={
            'message': drf_serializers.CharField(),
            'user_id': drf_serializers.IntegerField(),
            'verified': drf_serializers.BooleanField(),
            'access': drf_serializers.CharField(),
            'refresh': drf_serializers.CharField(),
        })},
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        google_id = serializer.validated_data["google_id"]
        profile_picture = serializer.validated_data.get("profile_picture")

        try:
            # CASE 1 — USER EXISTS
            user = User.objects.get(email=email)

            # A) User already linked with Google → verify Google ID
            if user.google_id:
                if user.google_id != google_id:
                    return Response({"error": "Google ID mismatch"}, status=401)

            # B) User exists but not linked → first Google login
            else:
                user.google_id = google_id
                user.save()

            # Update profile picture if sent
            if profile_picture:
                user.profile_picture = profile_picture
                user.save()

            # Make sure verified
            if not user.is_verified:
                user.is_verified = True
                user.save()

            # Generate tokens
            tokens = self.get_tokens_for_user(user)

            return Response({
                "message": "Login successful",
                "user_id": user.id,
                "verified": user.is_verified,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            })

        except User.DoesNotExist:
            # CASE 2 — NEW GOOGLE SIGNUP
            username = email.split("@")[0]

            user = User.objects.create(
                email=email,
                username=username,
                google_id=google_id,
                is_verified=True,
            )

            # No password for Google users
            user.set_unusable_password()

            if profile_picture:
                user.profile_picture = profile_picture

            user.save()

            # Generate tokens
            tokens = self.get_tokens_for_user(user)

            return Response({
                "message": "User created and logged in",
                "user_id": user.id,
                "verified": True,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            }, status=201)
