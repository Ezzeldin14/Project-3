import json
import hmac
import hashlib

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
    'is_void',
    'is_voided',
    'order.id',
    'owner',
    'pending',
    'source_data.pan',
    'source_data.sub_type',
    'source_data.type',
    'success',
]

def _resolve(data, dotted_key):
    keys = dotted_key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, '')
        else:
            return ''
    return value

def _to_str(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)

raw_body = """{"type": "TRANSACTION", "obj": {"id": 483702829, "pending": false, "amount_cents": 26700, "success": true, "is_auth": false, "is_capture": false, "is_standalone_payment": true, "is_voided": false, "is_refunded": false, "is_3d_secure": true, "integration_id": 5658071, "profile_id": 1161656, "has_parent_transaction": false, "order": {"id": 551815779, "created_at": "2026-06-23T18:20:06.791999", "delivery_needed": false, "merchant": {"id": 1161656, "created_at": "2026-05-08T19:21:44.673737", "phones": ["+201065397414"], "company_emails": null, "company_name": "GraduationProject", "state": "", "country": "EGY", "city": "Cairo", "postal_code": "", "street": ""}, "collector": null, "amount_cents": 26700, "shipping_data": {"id": 265389258, "first_name": "t135667756", "last_name": "Developer", "street": "NA", "building": "NA", "floor": "NA", "apartment": "NA", "city": "Alexandria", "state": "NA", "country": "EG", "email": "t135667756@gmail.com", "phone_number": "201000000000", "postal_code": "NA", "extra_description": "", "shipping_method": "UNK", "order_id": 551815779, "order": 551815779}, "currency": "USD", "is_payment_locked": false, "is_return": false, "is_cancel": false, "is_returned": false, "is_canceled": false, "merchant_order_id": null, "wallet_notification": null, "paid_amount_cents": 26700, "notify_user_with_email": false, "items": [], "order_url": "https://accept.paymob.com/standalone/?ref=i_LRR2QStqM281M1hrY25rblhMUkdlNVZ1UT09X2pIM1lIYWdmQ1BFdWJ2Y0RVRGhjQkE9PQ", "commission_fees": 0, "delivery_fees_cents": 0, "delivery_vat_cents": 0, "payment_method": "tbc", "merchant_staff_tag": null, "api_source": "OTHER", "data": {}, "payment_status": "PAID", "terminal_version": null, "payme_details": null}, "created_at": "2026-06-23T18:20:27.192795", "transaction_processed_callback_responses": [], "currency": "EGP", "source_data": {"pan": "1111", "type": "card", "tenure": null, "sub_type": "Visa"}, "api_source": "OTHER", "terminal_id": null, "merchant_commission": 0, "accept_fees": 0, "installment": null, "discount_details": [], "amount_cents_int": 26700, "is_void": false, "is_refund": false, "data": {"gateway_integration_pk": 5658071, "klass": "MigsPayment", "created_at": "2026-06-23T15:20:49.583668", "amount": 26700.0, "currency": "EGP", "migs_order": {"acceptPartialAmount": false, "amount": 267.0, "authenticationStatus": "AUTHENTICATION_SUCCESSFUL", "chargeback": {"amount": 0, "currency": "EGP"}, "creationTime": "2026-06-23T15:20:42.489Z", "currency": "EGP", "description": "PAYMOB GraduationProject", "id": "551815779", "lastUpdatedTime": "2026-06-23T15:20:49.417Z", "merchantAmount": 267.0, "merchantCategoryCode": "7299", "merchantCurrency": "EGP", "reference": "_483702829_551", "status": "CAPTURED", "totalAuthorizedAmount": 267.0, "totalCapturedAmount": 267.0, "totalRefundedAmount": 0.0}, "merchant": "TESTMERCH_C_25P", "migs_result": "SUCCESS", "migs_transaction": {"acquirer": {"batch": 20260623, "date": "0623", "id": "BMNF_S2I", "merchantId": "MERCH_C_25P", "settlementDate": "2026-06-23", "timeZone": "+0300", "transactionId": "123456789012345"}, "amount": 267.0, "authenticationStatus": "AUTHENTICATION_SUCCESSFUL", "authorizationCode": "196780", "currency": "EGP", "id": "483702829", "receipt": "617415196780", "reference": "_483702829", "source": "INTERNET", "stan": "196780", "terminal": "BMNF0509", "type": "PAYMENT"}, "txn_response_code": "APPROVED", "acq_response_code": "00", "message": "Approved", "merchant_txn_ref": "483702829", "order_info": "551815779", "receipt_no": "617415196780", "transaction_no": "123456789012345", "batch_no": 20260623, "authorize_id": "196780", "card_type": "VISA", "card_num": "411111xxxxxx1111", "secure_hash": "", "avs_result_code": "", "avs_acq_response_code": "00", "captured_amount": 267.0, "authorised_amount": 267.0, "refunded_amount": 0.0, "acs_eci": "05"}, "is_hidden": false, "payment_key_claims": {"exp": 1782231607, "extra": {}, "pmk_ip": "41.37.145.192", "user_id": 2230166, "currency": "EGP", "order_id": 551815779, "amount_cents": 26700, "billing_data": {"city": "Alexandria", "email": "t135667756@gmail.com", "floor": "NA", "state": "NA", "street": "NA", "country": "EG", "building": "NA", "apartment": "NA", "last_name": "Developer", "first_name": "t135667756", "postal_code": "NA", "phone_number": "+201000000000", "extra_description": "NA"}, "integration_id": 5658071, "lock_order_when_paid": false, "single_payment_attempt": false}, "error_occured": false, "is_live": false, "other_endpoint_reference": null, "refunded_amount_cents": 0, "refunded_amount_cents_int": 0, "source_id": -1, "is_captured": false, "captured_amount": 0, "captured_amount_int": 0, "settlement_amount_cents_int": 0, "merchant_staff_tag": null, "accept_fees_cents_int": 0, "vat_cents_int": 0, "vat_cents_float": null, "updated_at": "2026-06-23T18:20:49.592807", "is_settled": false, "bill_balanced": false, "is_bill": false, "owner": 2230166, "parent_transaction": null}}"""
payload = json.loads(raw_body)
txn = payload.get('obj')

concatenated = ''.join(_to_str(_resolve(txn, field)) for field in HMAC_FIELDS)
print("Concatenated:", concatenated)

secret = "D0AFA2B8C5CD1CAE78A9B8F0065BFDD8"
computed = hmac.new(
    key=secret.encode('utf-8'),
    msg=concatenated.encode('utf-8'),
    digestmod=hashlib.sha512,
).hexdigest()

print("Computed HMAC:", computed)
print("Expected HMAC:", "2c2a752cd1832a0f4ce85a0995b461d174bb9dcfcafcaa9d2a293b136d81f62a79a1a287b998fa3d0cdde19a23d83bd49ac4c1d07163d9ea2624a56d3ebae9bf")

