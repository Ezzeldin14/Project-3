from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    plan = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                'profile_picture', 'date_joined', 'is_verified',
                'plan', 'remaining_uses')
        read_only_fields = ('id', 'date_joined', 'is_verified', 'plan', 'remaining_uses')

    def get_plan(self, obj):
        from subscriptions.models import Subscription
        sub, _ = Subscription.objects.get_or_create(user=obj, defaults={'plan': 'FREE'})
        return sub.plan

    def get_remaining_uses(self, obj):
        from subscriptions.models import Subscription
        sub, _ = Subscription.objects.get_or_create(user=obj, defaults={'plan': 'FREE'})
        return sub.get_remaining_uses()


class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        from .models import EmailVerificationOTP

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid email address"})

        if user.is_verified:
            raise serializers.ValidationError({"detail": "Email is already verified"})

        try:
            verification_otp = EmailVerificationOTP.objects.filter(
                user=user,
                is_used=False
            ).latest('created_at')
        except EmailVerificationOTP.DoesNotExist:
            raise serializers.ValidationError({"detail": "No active OTP found. Please register again."})

        if verification_otp.is_expired():
            verification_otp.delete()
            raise serializers.ValidationError({"detail": "OTP has expired. Please register again."})

        if verification_otp.attempt_count >= 5:
            verification_otp.delete()
            raise serializers.ValidationError({"detail": "Too many failed attempts. Please register again."})

        if verification_otp.otp != otp:
            verification_otp.attempt_count += 1
            verification_otp.save()
            remaining = 5 - verification_otp.attempt_count
            raise serializers.ValidationError({
                "detail": f"Invalid OTP. {remaining} attempt(s) remaining."
            })

        user.is_verified = True
        user.save()

        verification_otp.is_used = True
        verification_otp.save()

        attrs['user'] = user
        return attrs


User = User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError({'detail': 'Enter email and password'})
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Wrong email or password'})
        
        if not user.is_verified:
            raise serializers.ValidationError({'detail': 'Email is not verified. Please check your inbox.'})
        
        if not user.check_password(password):
            raise serializers.ValidationError({'detail': 'Wrong email or password'})
        
        attrs['user'] = user
        return attrs









class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "No user with this email"})

        attrs["user"] = user
        return attrs


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")
        new_password = attrs.get("new_password")

        from .models import PasswordResetOTP

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid credentials"})

        try:
            reset_otp = PasswordResetOTP.objects.filter(
                user=user, 
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError({"detail": "No active OTP found. Please request a new one."})

        if reset_otp.is_expired():
            reset_otp.delete()
            raise serializers.ValidationError({"detail": "OTP has expired. Please request a new one."})

        if reset_otp.attempt_count >= 5:
            reset_otp.delete()
            raise serializers.ValidationError({"detail": "Too many failed attempts. Please request a new OTP."})

        if reset_otp.otp != otp:
            reset_otp.attempt_count += 1
            reset_otp.save()
            remaining = 5 - reset_otp.attempt_count
            raise serializers.ValidationError({
                "detail": f"Invalid OTP. {remaining} attempt(s) remaining."
            })

        user.set_password(new_password)
        user.save()

        reset_otp.is_used = True
        reset_otp.save()

        return attrs
    
    

class GoogleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    google_id = serializers.CharField()
    profile_picture = serializers.ImageField(required=False, allow_null=True)
