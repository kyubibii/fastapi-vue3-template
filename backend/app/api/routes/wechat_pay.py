"""
WeChat Pay API routes — reference implementation.

Provides endpoints for JSAPI prepay, payment/refund callbacks, order query,
order close, and refund application.  Downstream projects should customise the
business logic (e.g. updating their own payment-order tables) inside the
``# >>> YOUR BUSINESS LOGIC <<<`` markers.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, SessionDep
from app.middleware.audit_log import audit_log_exempt
from app.services.wechat_pay import (
    AmountInfo,
    NotificationVerificationError,
    PayerInfo,
    WechatPayClient,
    WxPaymentParams,
    build_payment_params,
    close_order,
    create_jsapi_prepay,
    create_refund,
    load_credentials_from_settings,
    query_order_by_out_trade_no,
    verify_and_decrypt_notification,
)
from app.services.wechat_pay.types import (
    JsapiPrepayRequest,
    OrderQueryResponse,
    RefundAmountInfo,
    RefundRequest,
    RefundResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wechat-pay", tags=["wechat-pay"])

# ── Helpers ────────────────────────────────────────────────────────────────────


async def _get_client() -> WechatPayClient:
    credentials = await load_credentials_from_settings()
    return WechatPayClient(credentials)


# ── Request / response schemas for the *route layer* ──────────────────────────


class PrepayRequestBody(BaseModel):
    """Simplified prepay request from the frontend / mini-program."""
    out_trade_no: str = Field(max_length=32)
    description: str = Field(max_length=127)
    total_amount: int = Field(gt=0, description="订单总金额，单位：分")
    openid: str
    attach: str | None = Field(default=None, max_length=128)
    time_expire: str | None = None


class PrepayResponseBody(BaseModel):
    payment_params: WxPaymentParams


class RefundRequestBody(BaseModel):
    """Simplified refund request from the admin panel."""
    transaction_id: str | None = None
    out_trade_no: str | None = None
    out_refund_no: str
    refund_amount: int = Field(gt=0, description="退款金额，单位：分")
    total_amount: int = Field(gt=0, description="原订单金额，单位：分")
    reason: str | None = None


# WeChat expects this exact JSON shape in the callback response
_NOTIFY_SUCCESS = {"code": "SUCCESS", "message": "成功"}
_NOTIFY_FAIL = {"code": "FAIL", "message": "失败"}


# ── 1. Create Prepay Order ─────────────────────────────────────────────────────


@router.post(
    "/prepay",
    response_model=PrepayResponseBody,
    response_model_by_alias=True,
    summary="创建预支付订单",
    description="调用微信 JSAPI 统一下单，返回小程序/JSAPI 调起支付所需的五个参数。",
)
async def prepay(
    body: PrepayRequestBody,
    session: SessionDep,
    current_user: CurrentUser,
) -> PrepayResponseBody:
    client = await _get_client()
    creds = client.credentials

    notify_url = f"{creds.notify_base_url}/api/v1/wechat-pay/notify/payment"

    request = JsapiPrepayRequest(
        appid=creds.app_id,
        mchid=creds.mch_id,
        description=body.description,
        out_trade_no=body.out_trade_no,
        time_expire=body.time_expire,
        attach=body.attach,
        notify_url=notify_url,
        amount=AmountInfo(total=body.total_amount),
        payer=PayerInfo(openid=body.openid),
    )

    # >>> YOUR BUSINESS LOGIC: persist the payment order record here <<<

    result = await create_jsapi_prepay(client, request)

    params = build_payment_params(
        app_id=creds.app_id,
        prepay_id=result.prepay_id,
        private_key=creds.private_key,
    )
    return PrepayResponseBody(payment_params=params)


# ── 2. Payment Callback ───────────────────────────────────────────────────────


@router.post(
    "/notify/payment",
    summary="支付结果回调通知",
    description="微信支付异步通知端点。验签 + 解密后处理业务逻辑。",
    include_in_schema=False,
)
@audit_log_exempt
async def notify_payment(request: Request) -> dict[str, str]:
    raw_body = await request.body()
    headers = {
        "Wechatpay-Timestamp": request.headers.get("Wechatpay-Timestamp", ""),
        "Wechatpay-Nonce": request.headers.get("Wechatpay-Nonce", ""),
        "Wechatpay-Signature": request.headers.get("Wechatpay-Signature", ""),
    }

    try:
        client = await _get_client()
        payload = verify_and_decrypt_notification(
            headers=headers,
            body=raw_body,
            public_key=client.credentials.public_key,
            api_v3_key=client.credentials.api_v3_key,
        )
    except NotificationVerificationError:
        logger.warning("Payment notification signature verification failed")
        return _NOTIFY_FAIL
    except Exception:
        logger.exception("Error processing payment notification")
        return _NOTIFY_FAIL

    logger.info(
        "Payment notification received: out_trade_no=%s trade_state=%s",
        payload.get("out_trade_no"),
        payload.get("trade_state"),
    )

    # >>> YOUR BUSINESS LOGIC: update order status, credit user, etc. <<<

    return _NOTIFY_SUCCESS


# ── 3. Refund Callback ────────────────────────────────────────────────────────


@router.post(
    "/notify/refund",
    summary="退款结果回调通知",
    description="微信退款异步通知端点。验签 + 解密后处理业务逻辑。",
    include_in_schema=False,
)
@audit_log_exempt
async def notify_refund(request: Request) -> dict[str, str]:
    raw_body = await request.body()
    headers = {
        "Wechatpay-Timestamp": request.headers.get("Wechatpay-Timestamp", ""),
        "Wechatpay-Nonce": request.headers.get("Wechatpay-Nonce", ""),
        "Wechatpay-Signature": request.headers.get("Wechatpay-Signature", ""),
    }

    try:
        client = await _get_client()
        payload = verify_and_decrypt_notification(
            headers=headers,
            body=raw_body,
            public_key=client.credentials.public_key,
            api_v3_key=client.credentials.api_v3_key,
        )
    except NotificationVerificationError:
        logger.warning("Refund notification signature verification failed")
        return _NOTIFY_FAIL
    except Exception:
        logger.exception("Error processing refund notification")
        return _NOTIFY_FAIL

    logger.info(
        "Refund notification received: out_refund_no=%s refund_status=%s",
        payload.get("out_refund_no"),
        payload.get("refund_status"),
    )

    # >>> YOUR BUSINESS LOGIC: update refund record status, etc. <<<

    return _NOTIFY_SUCCESS


# ── 4. Query Order ────────────────────────────────────────────────────────────


@router.get(
    "/orders/{out_trade_no}",
    response_model=OrderQueryResponse,
    summary="查询订单",
    description="通过商户订单号查询微信支付订单状态。",
)
async def get_order(
    out_trade_no: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> OrderQueryResponse:
    client = await _get_client()
    return await query_order_by_out_trade_no(client, out_trade_no)


# ── 5. Close Order ────────────────────────────────────────────────────────────


@router.post(
    "/orders/{out_trade_no}/close",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="关闭订单",
    description="关闭一笔未支付的订单。",
)
async def close(
    out_trade_no: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    client = await _get_client()
    await close_order(client, out_trade_no)


# ── 6. Create Refund ──────────────────────────────────────────────────────────


@router.post(
    "/refunds",
    response_model=RefundResponse,
    summary="申请退款",
    description="对已支付的订单发起退款申请。",
)
async def apply_refund(
    body: RefundRequestBody,
    session: SessionDep,
    current_user: CurrentUser,
) -> RefundResponse:
    client = await _get_client()
    creds = client.credentials

    notify_url = f"{creds.notify_base_url}/api/v1/wechat-pay/notify/refund"

    request = RefundRequest(
        transaction_id=body.transaction_id,
        out_trade_no=body.out_trade_no,
        out_refund_no=body.out_refund_no,
        reason=body.reason,
        notify_url=notify_url,
        amount=RefundAmountInfo(
            refund=body.refund_amount,
            total=body.total_amount,
        ),
    )

    # >>> YOUR BUSINESS LOGIC: persist refund record here <<<

    return await create_refund(client, request)
