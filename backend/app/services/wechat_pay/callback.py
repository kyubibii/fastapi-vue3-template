"""
WeChat Pay notification (callback) verification and decryption.

Handles both payment-result and refund-result notifications.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from cryptography.hazmat.primitives.asymmetric import rsa

from app.services.wechat_pay.crypto import aead_aes_256_gcm_decrypt, rsa_verify_sha256
from app.services.wechat_pay.types import WxPayNotification

logger = logging.getLogger(__name__)


class NotificationVerificationError(Exception):
    """Raised when the notification signature cannot be verified."""


def verify_and_decrypt_notification(
    *,
    headers: dict[str, str],
    body: str | bytes,
    public_key: rsa.RSAPublicKey,
    api_v3_key: str,
) -> dict[str, Any]:
    """Verify the callback signature and decrypt the resource payload.

    Parameters
    ----------
    headers:
        HTTP headers from the incoming request.  Must contain
        ``Wechatpay-Timestamp``, ``Wechatpay-Nonce``, and
        ``Wechatpay-Signature``.
    body:
        Raw request body (bytes or string).
    public_key:
        The WeChat Pay platform public key used to verify the signature.
    api_v3_key:
        The 32-byte API v3 key used to decrypt the AEAD resource.

    Returns
    -------
    dict
        Decrypted notification resource as a Python dict.

    Raises
    ------
    NotificationVerificationError
        If the signature does not match.
    """
    body_str = body if isinstance(body, str) else body.decode()

    timestamp = headers.get("Wechatpay-Timestamp", "")
    nonce = headers.get("Wechatpay-Nonce", "")
    signature = headers.get("Wechatpay-Signature", "")

    if not (timestamp and nonce and signature):
        raise NotificationVerificationError(
            "Missing required Wechatpay-* headers"
        )

    # Construct the verification message
    message = f"{timestamp}\n{nonce}\n{body_str}\n"
    if not rsa_verify_sha256(public_key, message, signature):
        raise NotificationVerificationError("Signature verification failed")

    # Parse the notification envelope and decrypt the resource
    notification = WxPayNotification.model_validate(json.loads(body_str))
    resource = notification.resource

    plaintext = aead_aes_256_gcm_decrypt(
        api_v3_key=api_v3_key,
        nonce=resource.nonce,
        ciphertext_b64=resource.ciphertext,
        associated_data=resource.associated_data or "",
    )

    return json.loads(plaintext)
