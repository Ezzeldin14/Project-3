import logging

import stripe
from django.conf import settings
from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer

from subscriptions.models import Subscription
from .models import Payment

logger = logging.getLogger(__name__)

# Configure stripe with the secret key from settings
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)


# ---------------------------------------------------------------------------
# PRO plan pricing — change these to match your Stripe product
# ---------------------------------------------------------------------------
PRO_PLAN_PRICE_CENTS = 999       # $9.99
PRO_PLAN_CURRENCY = 'usd'
PRO_PLAN_DESCRIPTION = 'PixelRevive PRO — Unlimited AI image processing'


class CreateCheckoutSessionView(APIView):
    """
    POST /api/payments/create-checkout-session/

    Creates a Stripe Checkout Session for the authenticated user to
    upgrade from FREE → PRO.  Returns the checkout URL that the Flutter
    app should open in a WebView / external browser.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: inline_serializer('CheckoutSessionResponse', fields={
            'checkout_url': drf_serializers.URLField(),
            'session_id': drf_serializers.CharField(),
        })},
    )
    def post(self, request):
        # Guard: already PRO
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'FREE'},
        )
        if subscription.is_pro:
            return Response(
                {"error": "You are already on the PRO plan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not stripe.api_key:
            return Response(
                {"error": "Payment system is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            # Build success / cancel URLs
            base_url = getattr(
                settings, 'STRIPE_SUCCESS_URL',
                f"{request.scheme}://{request.get_host()}/api/payments/success/",
            )
            cancel_url = getattr(
                settings, 'STRIPE_CANCEL_URL',
                f"{request.scheme}://{request.get_host()}/api/payments/cancel/",
            )

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',                    # one-time payment
                customer_email=request.user.email,
                client_reference_id=str(request.user.id),
                line_items=[{
                    'price_data': {
                        'currency': PRO_PLAN_CURRENCY,
                        'unit_amount': PRO_PLAN_PRICE_CENTS,
                        'product_data': {
                            'name': 'PixelRevive PRO Plan',
                            'description': PRO_PLAN_DESCRIPTION,
                        },
                    },
                    'quantity': 1,
                }],
                success_url=base_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(request.user.id),
                    'plan': 'PRO',
                },
            )

            # Create a PENDING payment record
            Payment.objects.create(
                user=request.user,
                amount=PRO_PLAN_PRICE_CENTS / 100,
                currency=PRO_PLAN_CURRENCY.upper(),
                payment_method='stripe',
                status='PENDING',
                description=PRO_PLAN_DESCRIPTION,
                reference_id=checkout_session.id,
            )

            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            logger.exception("Stripe error creating checkout session: %s", e)
            return Response(
                {"error": f"Payment provider error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class StripeWebhookView(APIView):
    """
    POST /api/payments/webhook/

    Stripe calls this endpoint to notify us of events (e.g. successful
    payment).  Must be configured in the Stripe Dashboard → Webhooks.
    """
    permission_classes = [AllowAny]      # Stripe can't send JWTs
    authentication_classes = []          # skip auth entirely

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

        if not webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret,
            )
        except ValueError:
            logger.warning("Invalid webhook payload")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid webhook signature")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self._handle_checkout_completed(session)

        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

    def _handle_checkout_completed(self, session: dict):
        """Upgrade the user to PRO and mark the payment as COMPLETED."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user_id = session.get('client_reference_id') or session.get('metadata', {}).get('user_id')
        if not user_id:
            logger.error("Webhook session missing user_id: %s", session.get('id'))
            return

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error("Webhook user not found: %s", user_id)
            return

        # Upgrade subscription to PRO
        subscription, _ = Subscription.objects.get_or_create(
            user=user,
            defaults={'plan': 'PRO'},
        )
        subscription.plan = 'PRO'
        subscription.stripe_customer_id = session.get('customer', '')
        subscription.save()

        # Mark Payment record as COMPLETED
        session_id = session.get('id')
        Payment.objects.filter(reference_id=session_id).update(status='COMPLETED')

        logger.info("User %s upgraded to PRO (session %s)", user.email, session_id)


class PaymentSuccessView(APIView):
    """
    GET /api/payments/success/?session_id=...

    Simple endpoint the browser redirects to after successful Stripe checkout.
    The Flutter app can detect this URL to close the WebView.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        session_id = request.query_params.get('session_id', '')
        return Response({
            'message': 'Payment successful! Your account has been upgraded to PRO.',
            'session_id': session_id,
        }, status=status.HTTP_200_OK)


class PaymentCancelView(APIView):
    """
    GET /api/payments/cancel/

    Stripe redirects here when the user cancels checkout.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'message': 'Payment was cancelled. You can try again anytime.',
        }, status=status.HTTP_200_OK)
