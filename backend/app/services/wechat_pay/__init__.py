"""
WeChat Pay v3 SDK — self-contained JSAPI payment toolkit.

Public API
----------
Credentials & client
    :class:`WechatPayCredentials`, :class:`WechatPayClient`,
    :func:`load_credentials_from_settings`

JSAPI prepay
    :func:`create_jsapi_prepay`, :func:`build_payment_params`

Order management
    :func:`query_order_by_out_trade_no`, :func:`close_order`

Refund
    :func:`create_refund`

Callback handling
    :func:`verify_and_decrypt_notification`,
    :exc:`NotificationVerificationError`

Low-level crypto (normally not needed directly)
    :func:`rsa_sign_sha256`, :func:`rsa_verify_sha256`,
    :func:`aead_aes_256_gcm_decrypt`,
    :func:`load_private_key`, :func:`load_public_key`
"""

from app.services.wechat_pay.callback import (
    NotificationVerificationError,
    verify_and_decrypt_notification,
)
from app.services.wechat_pay.client import (
    WechatPayClient,
    WechatPayCredentials,
    load_credentials_from_settings,
)
from app.services.wechat_pay.crypto import (
    aead_aes_256_gcm_decrypt,
    load_private_key,
    load_public_key,
    rsa_sign_sha256,
    rsa_verify_sha256,
)
from app.services.wechat_pay.jsapi import build_payment_params, create_jsapi_prepay
from app.services.wechat_pay.order import close_order, query_order_by_out_trade_no
from app.services.wechat_pay.refund import create_refund
from app.services.wechat_pay.types import (
    AmountInfo,
    JsapiPrepayRequest,
    JsapiPrepayResponse,
    OrderQueryResponse,
    PayerInfo,
    RefundRequest,
    RefundResponse,
    WxPaymentParams,
    WxPayNotification,
)

__all__ = [
    # Client
    "WechatPayClient",
    "WechatPayCredentials",
    "load_credentials_from_settings",
    # JSAPI
    "create_jsapi_prepay",
    "build_payment_params",
    # Order
    "query_order_by_out_trade_no",
    "close_order",
    # Refund
    "create_refund",
    # Callback
    "verify_and_decrypt_notification",
    "NotificationVerificationError",
    # Crypto
    "rsa_sign_sha256",
    "rsa_verify_sha256",
    "aead_aes_256_gcm_decrypt",
    "load_private_key",
    "load_public_key",
    # Types
    "AmountInfo",
    "JsapiPrepayRequest",
    "JsapiPrepayResponse",
    "OrderQueryResponse",
    "PayerInfo",
    "RefundRequest",
    "RefundResponse",
    "WxPaymentParams",
    "WxPayNotification",
]
