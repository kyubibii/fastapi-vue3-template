"""
Domestic refund operations.
"""

from __future__ import annotations

from app.services.wechat_pay.client import WechatPayClient
from app.services.wechat_pay.types import RefundRequest, RefundResponse


async def create_refund(
    client: WechatPayClient,
    request: RefundRequest,
) -> RefundResponse:
    """Apply for a domestic refund via ``POST /v3/refund/domestic/refunds``."""
    response = await client.request(
        "POST",
        "/v3/refund/domestic/refunds",
        json_body=request.model_dump(exclude_none=True),
    )
    response.raise_for_status()
    return RefundResponse.model_validate(response.json())
