from typing import Any

import httpx


def calculate_bonus_and_points(sale_closed: bool, sale_value: float, bonus_percentage: float) -> tuple[float, int]:
    if sale_closed:
        bonus = round(sale_value * (bonus_percentage / 100), 2)
        points = int(sale_value // 100)
        return bonus, points
    return 0.0, 30


async def send_to_agendor(client_payload: dict[str, Any], token: str | None) -> None:
    if not token:
        return
    headers = {"Authorization": f"Token {token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.agendor.com.br/v3/persons",
            json=client_payload,
            headers=headers,
        )


async def send_to_autentique(contract_payload: dict[str, Any], token: str | None) -> None:
    if not token:
        return
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://api.autentique.com.br/v2/graphql",
            json=contract_payload,
            headers=headers,
        )
