import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers

from .models import Subscription
from .serializers import SubscriptionSerializer, UsageRecordSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class SubscriptionStatusView(APIView):
    """
    GET /api/subscriptions/status/

    Returns the authenticated user's current plan, remaining AI-feature
    uses, and when the quota next renews.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: SubscriptionSerializer})
    def get(self, request):
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'FREE'},
        )
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UsageHistoryView(APIView):
    """
    GET /api/subscriptions/usage/

    Returns the user's recent AI-feature usage records (last 20).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UsageRecordSerializer(many=True)})
    def get(self, request):
        records = request.user.usage_records.all()[:20]
        serializer = UsageRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------------------------------------------------------ #
#  Paymob transaction webhook                                        #
# ------------------------------------------------------------------ #

# The 21 fields Paymob includes in the HMAC calculation, in order.
HMAC_FIELDS = [
    'amount_cents',
    'created_at',
    'currency',
    'error_occured',
    'has_parent_transaction',
    'id',
    'integration_id',
    'is_3d_secure',
    'is_auth',
    'is_capture',
    'is_refunded',
    'is_standalone_payment',
    'is_voided',
    'order.id',
    'owner',
    'pending',
    'source_data.pan',
    'source_data.sub_type',
    'source_data.type',
    'success',
]


def _resolve(data: dict, dotted_key: str):
    """Resolve a dotted key like 'order.id' from a nested dict."""
    keys = dotted_key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, '')
        else:
            return ''
    return value


def _to_str(value) -> str:
    """Convert a value to string matching Paymob's format.
    Booleans must be lowercase 'true'/'false' (not Python's 'True'/'False').
    """
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def _verify_hmac(txn_data: dict, received_hmac: str) -> bool:
    """
    Build the concatenated string from the transaction object,
    compute HMAC-SHA512 with the Paymob secret, and compare.
    """
    secret = getattr(settings, 'PAYMOB_HMAC_SECRET', '')
    if not secret:
        logger.error('PAYMOB_HMAC_SECRET is not configured.')
        return False

    concatenated = ''.join(_to_str(_resolve(txn_data, field)) for field in HMAC_FIELDS)

    computed = hmac.new(
        key=secret.encode('utf-8'),
        msg=concatenated.encode('utf-8'),
        digestmod=hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(computed, received_hmac)


@method_decorator(csrf_exempt, name='dispatch')
class PaymobWebhookView(APIView):
    """
    POST /api/subscriptions/paymob-webhook/

    Called by Paymob servers after a payment is processed.
    Verifies the HMAC signature and upgrades the user to PRO.

    Paymob sends:
    {
        "obj": { ... transaction data ... },
        "hmac": "xxxxxxx"
    }

    The user is identified by billing_data.email inside the
    transaction object. The frontend must pass the user's
    registered email when creating the Paymob payment.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=inline_serializer('PaymobWebhookRequest', fields={
            'obj': inline_serializer('PaymobTransaction', fields={
                'success': drf_serializers.BooleanField(),
                'amount_cents': drf_serializers.IntegerField(),
                'order': inline_serializer('PaymobOrder', fields={
                    'id': drf_serializers.CharField(),
                }),
                'billing_data': inline_serializer('PaymobBillingData', fields={
                    'email': drf_serializers.EmailField(help_text='The user email registered in the app'),
                }),
            }),
            'hmac': drf_serializers.CharField(help_text='Security signature from Paymob'),
        }),
        responses={
            200: inline_serializer('PaymobWebhookResponse', fields={
                'status': drf_serializers.CharField(),
            }),
        },
    )
    def post(self, request):
        # Log the FULL raw request body to see exactly what Paymob sends
        logger.error('Paymob webhook received. RAW BODY=%s', request.body.decode('utf-8', errors='replace')[:5000])

        # Parse raw body
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            logger.error('Paymob webhook: invalid JSON payload.')
            return Response(
                {'error': 'Invalid JSON payload.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.error('Paymob webhook: payload keys=%s', list(payload.keys()))
        logger.error('Paymob webhook: query params=%s', dict(request.query_params))

        # HMAC can be in query params (?hmac=xxx) or in the JSON body
        received_hmac = (
            request.query_params.get('hmac', '')
            or payload.get('hmac', '')
        )

        # Transaction data can be under "obj" key or directly in the body
        txn = payload.get('obj', None)
        if txn is None:
            txn = payload

        if not txn or not received_hmac:
            logger.error('Paymob webhook: missing txn data or hmac. hmac=%s, txn_keys=%s',
                         bool(received_hmac), list(txn.keys()) if isinstance(txn, dict) else 'not a dict')
            return Response(
                {'error': 'Missing transaction data or "hmac".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Verify HMAC ----
        if not _verify_hmac(txn, received_hmac):
            logger.warning('Paymob webhook HMAC verification failed.')
            return Response(
                {'error': 'Invalid HMAC signature.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        logger.error('Paymob webhook: HMAC verified OK.')

        # ---- Check payment success ----
        success = txn.get('success', False)
        logger.error('Paymob webhook: success=%s (type=%s), txn id=%s', success, type(success).__name__, txn.get('id'))

        if not success:
            logger.error('Paymob webhook: payment not successful, ignoring.')
            return Response({'status': 'ignored (not successful)'}, status=status.HTTP_200_OK)

        # ---- Identify the user ----
        # Paymob puts the email in shipping_data and payment_key_claims, NOT order.billing_data
        order_data = txn.get('order', {}) or {}
        shipping_data = order_data.get('shipping_data', {}) or {}
        payment_claims = txn.get('payment_key_claims', {}) or {}
        claims_billing = payment_claims.get('billing_data', {}) or {}

        # Try email from multiple locations where Paymob puts it
        user_email = (
            shipping_data.get('email', '')
            or claims_billing.get('email', '')
            or order_data.get('merchant_order_id', '')
            or txn.get('merchant_order_id', '')
        )

        # Filter out Paymob's default "NA" value
        if user_email == 'NA':
            user_email = ''

        logger.error('Paymob webhook: resolved user_email=%s', user_email)

        if not user_email:
            logger.error('Paymob webhook: cannot identify user, txn id=%s', txn.get('id'))
            return Response(
                {'error': 'Cannot identify user — no email in billing_data.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            logger.error('Paymob webhook: user %s not found, txn id=%s', user_email, txn.get('id'))
            return Response(
                {'error': f'User with email {user_email} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info('Paymob webhook: found user %s (id=%s)', user_email, user.id)

        # ---- Upgrade to PRO ----
        try:
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                defaults={'plan': 'FREE'},
            )
            logger.info('Paymob webhook: subscription plan=%s, created=%s', subscription.plan, created)

            order_id = str(_resolve(txn, 'order.id'))
            subscription.plan = 'PRO'
            subscription.paymob_order_id = order_id
            subscription.save(update_fields=['plan', 'paymob_order_id', 'updated_at'])

            logger.info('User %s upgraded to PRO via Paymob order %s', user_email, order_id)
            return Response({'status': 'user upgraded to PRO'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception('Paymob webhook: failed to upgrade user %s: %s', user_email, str(e))
            return Response(
                {'error': f'Failed to upgrade user: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ------------------------------------------------------------------ #
#  Verify payment (called by the Flutter app with JWT)               #
# ------------------------------------------------------------------ #

class VerifyPaymentView(APIView):
    """
    POST /api/subscriptions/verify-payment/

    Called by the Flutter app after the user completes a Paymob payment.
    The user is already authenticated with JWT, so we know who they are.

    Expected JSON body:
    {
        "transaction_id": "458534320"
    }
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer('VerifyPaymentRequest', fields={
            'transaction_id': drf_serializers.CharField(help_text='Paymob transaction ID'),
        }),
        responses={
            200: inline_serializer('VerifyPaymentResponse', fields={
                'status': drf_serializers.CharField(),
                'plan': drf_serializers.CharField(),
            }),
        },
    )
    def post(self, request):
        transaction_id = request.data.get('transaction_id', '')

        if not transaction_id:
            return Response(
                {'error': 'Missing transaction_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Upgrade the authenticated user to PRO
        subscription, _ = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': 'FREE'},
        )
        subscription.plan = 'PRO'
        subscription.paymob_order_id = str(transaction_id)
        subscription.save(update_fields=['plan', 'paymob_order_id', 'updated_at'])

        logger.info('User %s upgraded to PRO via verify-payment, txn=%s', request.user.email, transaction_id)
        return Response({
            'status': 'user upgraded to PRO',
            'plan': 'PRO',
        }, status=status.HTTP_200_OK)

