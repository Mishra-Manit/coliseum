# Telegram Notifications

Simple message-based notification service for Coliseum trading system.

## Usage

### Standalone

```python
from coliseum.services.telegram import create_telegram_client

async with create_telegram_client(bot_token=token, chat_id=chat_id) as client:
    message = "✅ <b>Trade Executed</b>\n\nTicker: PRES-TRUMP-WIN\nContracts: 100\nPrice: $0.52"
    result = await client.send_alert(message)
    
    if result.success:
        print(f"Sent! Message ID: {result.message_id}")
    else:
        print(f"Failed: {result.error}")
```

### Agent Integration (Pattern 1: Dependencies)

```python
from coliseum.services.telegram import TelegramClient

class TraderDependencies(BaseModel):
    kalshi_client: KalshiClient
    telegram_client: TelegramClient | None = None  # Optional
    config: Settings

# Usage
async with create_telegram_client(bot_token=token, chat_id=chat_id) as telegram_client:
    deps = TraderDependencies(kalshi_client=kalshi, telegram_client=telegram_client, ...)
    result = await trader_agent.run("Execute trade", deps=deps)
```

### Agent Integration (Pattern 2: Tool)

```python
@trader_agent.tool
async def send_telegram_alert(ctx: RunContext[TraderDependencies], message: str) -> dict:
    """Send telegram notification message."""
    if not ctx.deps.telegram_client:
        return {"sent": False, "reason": "not configured"}
    
    result = await ctx.deps.telegram_client.send_alert(message)
    return {"sent": result.success, "message_id": result.message_id, "error": result.error}
```

### Direct Integration (Non-Agent)

```python
async def execute_trade(trade_params):
    # Execute trade...
    
    if telegram_client:
        message = f"✅ <b>Trade Executed</b>\n\nTicker: {ticker}\nContracts: {contracts}\nPrice: ${price}"
        await telegram_client.send_alert(message)
```

## Message Formatting

Messages support HTML formatting via Telegram's parse_mode. Format your own messages:

### Trade Execution
```python
message = """✅ <b>Trade Executed</b>

Ticker: MARKET-ABC
Side: YES
Contracts: 100
Price: $0.52
Total Cost: $52.00
Edge: +8.0%"""

await client.send_alert(message)
```

### Risk Warning
```python
message = """🚨 <b>Risk Warning</b>

Limit Type: Max Position Exposure
Current: 8.5%
Limit: 10.0%

Action: Reduce positions"""

await client.send_alert(message)
```

### Position Closed
```python
pnl_emoji = "✅" if realized_pnl > 0 else "❌"
message = f"""{pnl_emoji} <b>Position Closed</b>

Ticker: {ticker}
Side: {side}
Contracts: {contracts}
Realized P&L: ${realized_pnl:.2f} ({realized_pct:.1%})
Reason: {reason}"""

await client.send_alert(message)
```

## Architecture

### Files
- `coliseum/services/telegram/__init__.py` - Public API exports
- `coliseum/services/telegram/client.py` - Async client with retry logic
- `coliseum/services/telegram/models.py` - NotificationResult model
- `coliseum/services/telegram/exceptions.py` - Exception hierarchy
- `coliseum/services/telegram/config.py` - TelegramConfig model

### Features
- ✅ Simple retry logic (2 attempts, 2-second delay)
- ✅ HTML message formatting support
- ✅ Async context manager pattern
- ✅ Full Pydantic validation
- ✅ Graceful degradation (optional client)
- ✅ Automatic bot verification on connect

### Exception Hierarchy
```
TelegramError
├── TelegramAuthError (401)
├── TelegramRateLimitError (429)
├── TelegramNetworkError (network issues)
└── TelegramConfigError (validation errors)
```

## Testing

```bash
cd backend
source venv/bin/activate

# Manual test
python -c "
import asyncio
from coliseum.services.telegram import create_telegram_client

async def test():
    async with create_telegram_client(bot_token='YOUR_TOKEN', chat_id='YOUR_CHAT_ID') as client:
        result = await client.send_alert('🤖 <b>Test Message</b>\n\nSystem is working!')
        print(f'Success: {result.success}')

asyncio.run(test())
"
```

## Best Practices

1. **Always optional**: `telegram_client: TelegramClient | None = None`
2. **Check before use**: `if telegram_client: await telegram_client.send_alert(alert)`
3. **Graceful degradation**: System works without Telegram configured
4. **Filter alerts**: Use `config.yaml` to control alert types
5. **Never block**: All operations are async

## Common Patterns

### Conditional Client Creation
```python
if settings.telegram_bot_token and settings.telegram_chat_id:
    telegram_client = await create_telegram_client(...)
else:
    telegram_client = None  # Graceful degradation
```

### Error Handling with Alerts
```python
try:
    # Risky operation
    pass
except Exception as e:
    if telegram_client:
        message = f"🚨 <b>Critical Error</b>\n\nError: {str(e)}\nContext: Trade execution"
        await telegram_client.send_alert(message)
    raise
```

## API Reference

### `create_telegram_client(bot_token, chat_id, config)`
Factory function to create a TelegramClient instance.

**Parameters:**
- `bot_token: str | None` - Telegram bot token
- `chat_id: str | None` - Default chat ID for messages
- `config: TelegramConfig | None` - Optional config object

**Returns:** `TelegramClient` instance

### `TelegramClient.send_alert(message, chat_id)`
Send a message with automatic retry (2 attempts).

**Parameters:**
- `message: str` - Message text (supports HTML formatting)
- `chat_id: str | None` - Override default chat ID

**Returns:** `NotificationResult` with success status, message_id, and error details

### `NotificationResult`
Result object from send_alert().

**Fields:**
- `success: bool` - Whether message was sent
- `message_id: int | None` - Telegram message ID
- `recipient: str` - Chat ID message was sent to
- `sent_at: datetime` - Timestamp
- `error: str | None` - Error message if failed
- `retry_count: int` - Number of retries attempted

### `TelegramConfig`
Configuration model.

**Fields:**
- `bot_token: str` - Bot token (default: "")
- `default_chat_id: str` - Default chat ID (default: "")
- `max_retries: int` - Max retry attempts (default: 3)
- `timeout_seconds: float` - Request timeout (default: 30.0)
- `parse_mode: str` - Message parse mode (default: "HTML")

---

**Status**: ✅ Production ready  
**Dependencies**: `python-telegram-bot>=21.0.1`  
**Pattern**: Simple message-based API with async context manager
