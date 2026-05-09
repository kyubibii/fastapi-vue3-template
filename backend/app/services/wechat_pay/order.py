"""
Order query and close operations.
"""

from __future__ import annotations

from app.services.wechat_pay.client import WechatPayClient
from app.services.wechat_pay.types import OrderQueryResponse


async def query_order_by_out_trade_no(
    client: WechatPayClient,
    out_trade_no: str,
) -> OrderQueryResponse:
    """Query order status via ``GET /v3/pay/transactions/out-trade-no/{out_trade_no}``."""
    path = (
        f"/v3/pay/transactions/out-trade-no/{out_trade_no}"
        f"?mchid={client.credentials.mch_id}"
    )
    response = await client.request("GET", path)
    response.raise_for_status()
    return OrderQueryResponse.model_validate(response.json())


async def close_order(
    client: WechatPayClient,
    out_trade_no: str,
) -> None:
    """Close an unpaid order via ``POST /v3/pay/transactions/out-trade-no/{out_trade_no}/close``.

    WeChat returns ``204 No Content`` on success.
    """
    path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}/close"
    response = await client.request(
        "POST",
        path,
        json_body={"mchid": client.credentials.mch_id},
        verify_response=False,
    )
    response.raise_for_status()
