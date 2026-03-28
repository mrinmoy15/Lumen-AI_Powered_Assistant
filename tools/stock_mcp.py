# stock_mcp.py
import os
import httpx
import json
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict

# -------------------------
# Constants
# -------------------------
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

mcp = FastMCP("stock_mcp")

# -------------------------
# Shared HTTP client helper
# -------------------------
async def _fetch_alpha_vantage(params: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(ALPHA_VANTAGE_BASE_URL, params=params)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"API request failed with status {e.response.status_code}")
        except httpx.TimeoutException:
            raise ValueError("Request timed out. Please try again.")

# -------------------------
# Input model
# -------------------------
class StockPriceInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    symbol: str = Field(
        ...,
        description="Stock ticker symbol (e.g. 'AAPL', 'TSLA', 'GOOGL')",
        min_length=1,
        max_length=10
    )

    @field_validator('symbol')
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper()

# -------------------------
# Tool
# -------------------------
@mcp.tool(
    name="stock_get_price",
    annotations={
        "title": "Get Latest Stock Price",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def stock_get_price(params: StockPriceInput) -> str:
    """Fetch the latest stock price for a given ticker symbol using Alpha Vantage.

    Args:
        params (StockPriceInput): Input containing:
            - symbol (str): Stock ticker symbol (e.g. 'AAPL', 'TSLA')

    Returns:
        str: JSON-formatted response containing:
            - symbol (str): Ticker symbol
            - price (str): Latest trading price
            - change (str): Price change
            - change_percent (str): Percentage change
            - volume (str): Trading volume
            - latest_trading_day (str): Date of latest trading day
    """
    data = await _fetch_alpha_vantage({
        "function": "GLOBAL_QUOTE",
        "symbol": params.symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    })

    quote = data.get("Global Quote", {})
    if not quote:
        return json.dumps({"error": f"No data found for symbol '{params.symbol}'. Check the ticker is valid."})

    return json.dumps({
        "symbol": quote.get("01. symbol"),
        "price_usd": float(quote.get("05. price", 0)),  # renamed + cast to float
        "change_usd": float(quote.get("09. change", 0)),
        "change_percent": quote.get("10. change percent"),
        "volume": int(quote.get("06. volume", 0)),
        "latest_trading_day": quote.get("07. latest trading day")
    }, indent=2)


if __name__ == "__main__":
    mcp.run()  # stdio transport (for local use)
    # mcp.run(transport="streamable_http", port=8000)  # uncomment for remote