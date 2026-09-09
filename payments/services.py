import uuid
import requests
from django.conf import settings
from .models import Payment


def initiate_payment(payment: Payment, phone: str = "") -> dict:
    mode = getattr(settings, "PAYMENT_MODE", "sandbox")
    has_orange = bool(getattr(settings, "ORANGE_CLIENT_ID", ""))
    has_mtn = bool(getattr(settings, "MTN_SUBSCRIPTION_KEY", ""))

    if mode == "sandbox" and not (has_orange or has_mtn):
        return _simulate(payment)

    if payment.provider == "ORANGE_MONEY" and has_orange:
        return _orange_money(payment, phone)
    if payment.provider == "MTN_MOMO" and has_mtn:
        return _mtn_momo(payment, phone)

    return _simulate(payment)


def _simulate(payment: Payment) -> dict:
    tx = f"SIM-{uuid.uuid4().hex[:12].upper()}"
    payment.transaction_id = tx
    payment.status = "PENDING"
    payment.provider_response = {
        "simulated": True,
        "message": "Paiement sandbox — utilisez simulate_success",
    }
    payment.save(
        update_fields=["transaction_id", "status", "provider_response", "updated_at"]
    )
    return {
        "ok": True,
        "simulated": True,
        "transaction_id": tx,
        "payment_url": None,
    }


def _orange_money(payment: Payment, phone: str) -> dict:
    token_url = "https://api.orange.com/oauth/v3/token"
    auth = (settings.ORANGE_CLIENT_ID, settings.ORANGE_CLIENT_SECRET)
    r = requests.post(
        token_url,
        auth=auth,
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    r.raise_for_status()
    access_token = r.json()["access_token"]

    order_id = f"COV-{payment.id}-{uuid.uuid4().hex[:8]}"
    frontend = getattr(settings, "FRONTEND_URL", "http://127.0.0.1:8000")
    backend = getattr(settings, "BACKEND_URL", "http://127.0.0.1:8000")

    payload = {
        "merchant_key": settings.ORANGE_MERCHANT_KEY,
        "currency": payment.currency or "XAF",
        "order_id": order_id,
        "amount": int(payment.amount),
        "return_url": f"{frontend}/my-bookings/",
        "cancel_url": f"{frontend}/my-bookings/",
        "notif_url": f"{backend}/api/payments/webhook/orange/",
        "lang": "fr",
        "reference": str(payment.booking_id),
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    url = f"{settings.ORANGE_API_URL.rstrip('/')}/webpayment"
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    data = resp.json() if resp.content else {}

    payment.transaction_id = data.get("pay_token") or order_id
    payment.provider_response = data
    payment.status = "PENDING"
    payment.save(
        update_fields=["transaction_id", "provider_response", "status", "updated_at"]
    )
    return {
        "ok": resp.ok,
        "simulated": False,
        "transaction_id": payment.transaction_id,
        "payment_url": data.get("payment_url"),
        "raw": data,
    }


def _mtn_momo(payment: Payment, phone: str) -> dict:
    token_url = f"{settings.MTN_API_URL.rstrip('/')}/collection/token/"
    headers = {"Ocp-Apim-Subscription-Key": settings.MTN_SUBSCRIPTION_KEY}
    r = requests.post(
        token_url,
        headers=headers,
        auth=(settings.MTN_API_USER, settings.MTN_API_KEY),
        timeout=30,
    )
    r.raise_for_status()
    access_token = r.json()["access_token"]

    reference_id = str(uuid.uuid4())
    clean_phone = (phone or "").replace("+", "").replace(" ", "")
    currency = (
        "EUR"
        if getattr(settings, "MTN_TARGET_ENV", "sandbox") == "sandbox"
        else (payment.currency or "XAF")
    )
    payload = {
        "amount": str(int(payment.amount)),
        "currency": currency,
        "externalId": str(payment.id),
        "payer": {"partyIdType": "MSISDN", "partyId": clean_phone},
        "payerMessage": "Covoiturage",
        "payeeNote": f"Booking {payment.booking_id}",
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Reference-Id": reference_id,
        "X-Target-Environment": settings.MTN_TARGET_ENV,
        "Ocp-Apim-Subscription-Key": settings.MTN_SUBSCRIPTION_KEY,
        "Content-Type": "application/json",
    }
    url = f"{settings.MTN_API_URL.rstrip('/')}/collection/v1_0/requesttopay"
    resp = requests.post(url, json=payload, headers=headers, timeout=30)

    payment.transaction_id = reference_id
    payment.provider_response = {
        "status_code": resp.status_code,
        "body": (resp.text or "")[:500],
    }
    payment.status = "PENDING"
    payment.save(
        update_fields=["transaction_id", "provider_response", "status", "updated_at"]
    )
    return {
        "ok": resp.status_code in (200, 202),
        "simulated": False,
        "transaction_id": reference_id,
        "payment_url": None,
    }