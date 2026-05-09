"""
Pydantic models for WeChat Pay v3 API requests and responses.

Field names use ``alias`` to match the snake_case ↔ WeChat JSON mapping.
All models use ``populate_by_name=True`` so both Python attribute names
and their JSON aliases are accepted.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared / reusable components
# ---------------------------------------------------------------------------

class AmountInfo(BaseModel):
    """Order amount — *total* is in **fen** (分)."""
    total: int
    currency: str = "CNY"


class PayerInfo(BaseModel):
    openid: str


class StoreInfo(BaseModel):
    id: str
    name: str | None = None
    area_code: str | None = None
    address: str | None = None


class SceneInfo(BaseModel):
    payer_client_ip: str
    device_id: str | None = None
    store_info: StoreInfo | None = None


class GoodsDetail(BaseModel):
    merchant_goods_id: str
    wechatpay_goods_id: str | None = None
    goods_name: str | None = None
    quantity: int
    unit_price: int


class CouponDetail(BaseModel):
    cost_price: int | None = None
    invoice_id: str | None = None
    goods_detail: list[GoodsDetail] | None = None


class SettleInfo(BaseModel):
    profit_sharing: bool | None = None


# ---------------------------------------------------------------------------
# JSAPI Prepay
# ---------------------------------------------------------------------------

class JsapiPrepayRequest(BaseModel):
    """POST /v3/pay/transactions/jsapi request body."""
    appid: str
    mchid: str
    description: str = Field(max_length=127)
    out_trade_no: str = Field(max_length=32)
    time_expire: str | None = None
    attach: str | None = Field(default=None, max_length=128)
    notify_url: str
    goods_tag: str | None = None
    support_fapiao: bool | None = None
    amount: AmountInfo
    payer: PayerInfo
    detail: CouponDetail | None = None
    scene_info: SceneInfo | None = None
    settle_info: SettleInfo | None = None


class JsapiPrepayResponse(BaseModel):
    prepay_id: str


# ---------------------------------------------------------------------------
# wx.requestPayment parameters (returned to mini-program / JSAPI caller)
# ---------------------------------------------------------------------------

class WxPaymentParams(BaseModel):
    """The five fields needed by ``wx.requestPayment()``."""
    time_stamp: str = Field(alias="timeStamp")
    nonce_str: str = Field(alias="nonceStr")
    package: str
    sign_type: str = Field(alias="signType", default="RSA")
    pay_sign: str = Field(alias="paySign")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Order query
# ---------------------------------------------------------------------------

class OrderAmount(BaseModel):
    total: int | None = None
    payer_total: int | None = None
    currency: str | None = None
    payer_currency: str | None = None


class OrderPayer(BaseModel):
    openid: str | None = None


class OrderQueryResponse(BaseModel):
    appid: str | None = None
    mchid: str | None = None
    out_trade_no: str | None = None
    transaction_id: str | None = None
    trade_type: str | None = None
    trade_state: str | None = None
    trade_state_desc: str | None = None
    bank_type: str | None = None
    attach: str | None = None
    success_time: str | None = None
    amount: OrderAmount | None = None
    payer: OrderPayer | None = None


# ---------------------------------------------------------------------------
# Close order
# ---------------------------------------------------------------------------

class CloseOrderRequest(BaseModel):
    mchid: str


# ---------------------------------------------------------------------------
# Refund
# ---------------------------------------------------------------------------

class RefundAmountInfo(BaseModel):
    refund: int
    total: int
    currency: str = "CNY"


class RefundGoodsDetail(BaseModel):
    merchant_goods_id: str
    wechatpay_goods_id: str | None = None
    goods_name: str | None = None
    unit_price: int
    refund_amount: int
    refund_quantity: int


class RefundRequest(BaseModel):
    """POST /v3/refund/domestic/refunds request body."""
    transaction_id: str | None = None
    out_trade_no: str | None = None
    out_refund_no: str
    reason: str | None = None
    notify_url: str | None = None
    funds_account: str | None = None
    amount: RefundAmountInfo
    goods_detail: list[RefundGoodsDetail] | None = None


class RefundResponseAmount(BaseModel):
    total: int | None = None
    refund: int | None = None
    payer_total: int | None = None
    payer_refund: int | None = None
    settlement_refund: int | None = None
    settlement_total: int | None = None
    discount_refund: int | None = None
    currency: str | None = None


class RefundResponse(BaseModel):
    refund_id: str | None = None
    out_refund_no: str | None = None
    transaction_id: str | None = None
    out_trade_no: str | None = None
    channel: str | None = None
    user_received_account: str | None = None
    success_time: str | None = None
    create_time: str | None = None
    status: str | None = None
    amount: RefundResponseAmount | None = None


# ---------------------------------------------------------------------------
# Callback / Notification
# ---------------------------------------------------------------------------

class NotificationResource(BaseModel):
    """Encrypted resource inside a WeChat Pay notification."""
    original_type: str | None = None
    algorithm: str
    ciphertext: str
    associated_data: str | None = None
    nonce: str


class WxPayNotification(BaseModel):
    """Top-level WeChat Pay notification envelope."""
    id: str
    create_time: str
    resource_type: str | None = None
    event_type: str
    summary: str | None = None
    resource: NotificationResource
