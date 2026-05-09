"""
JSAPI / Mini-program prepay order creation and payment-parameter generation.
"""

from __future__ import annotations

import secrets
import time

from cryptography.hazmat.primitives.asymmetric import rsa

from app.services.wechat_pay.client import WechatPayClient
from app.services.wechat_pay.crypto import rsa_sign_sha256
from app.services.wechat_pay.types import (
    JsapiPrepayRequest,
    JsapiPrepayResponse,
    WxPaymentParams,
)


async def create_jsapi_prepay(
    client: WechatPayClient,
    request: JsapiPrepayRequest,
) -> JsapiPrepayResponse:
    """Call ``/v3/pay/transactions/jsapi`` and return the ``prepay_id``."""
    response = await client.request(
        "POST",
        "/v3/pay/transactions/jsapi",
        json_body=request.model_dump(exclude_none=True),
    )
    response.raise_for_status()
    return JsapiPrepayResponse.model_validate(response.json())


def build_payment_params(
    app_id: str,
    prepay_id: str,
    private_key: rsa.RSAPrivateKey,
) -> WxPaymentParams:
    """Build the five fields required by ``wx.requestPayment()``.

    The signature message layout for the mini-program / JSAPI caller is::

        APP_ID\\n
        TIMESTAMP\\n
        NONCE\\n
        package_value\\n
    """
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    package = f"prepay_id={prepay_id}"
    sign_message = f"{app_id}\n{timestamp}\n{nonce}\n{package}\n"
    pay_sign = rsa_sign_sha256(private_key, sign_message)
    return WxPaymentParams(
        timeStamp=timestamp,
        nonceStr=nonce,
        package=package,
        signType="RSA",
        paySign=pay_sign,
    )
