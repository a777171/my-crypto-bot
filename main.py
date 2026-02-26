import time
import requests
import os

# تنظیمات از بخش Environment Variables سرور خوانده می‌شود
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# لیست ارزهای اختصاصی ۲۰۲۶
WATCHLIST = [
    'immutable-x', 'thorchain', 'cyberconnect', 'api3', 'compound-governance-token',
    'tezos', 'zilliqa', 'ondo-finance', 'aptos', 'polkadot', 'optimism', 'near',
    'pyth-network', 'polygon-ecosystem-token', 'arbitrum', 'jasmycoin',
    'worldcoin-wld', 'floki', 'tellor', 'rocket-pool', 'yield-guild-games', 
    'avalanche-2', 'uniswap', 'injective-protocol', 'sui', 'sei-network', 
    'celestia', 'render-token', 'bittensor', 'pepe', 'solana', 'dogecoin', 'chainlink'
]

def get_tether_price():
    try:
        url = "https://api.nobitex.ir"
        res = requests.get(url, timeout=10).json()
        return int(res['lastTradePrice']) // 10 if res.get('status') == 'ok' else "نوسانی"
    except: return "نامشخص"

def get_crypto_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://api.coingecko.com"
    try:
        # دریافت ۲۰ ارز اول و لیست اختصاصی
        p_top = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 20, 'page': 1}
        top_m = requests.get(url, params=p_top, headers=headers, timeout=15).json()
        p_watch = {'vs_currency': 'usd', 'ids': ','.join(WATCHLIST)}
        watch_m = requests.get(url, params=p_watch, headers=headers, timeout=15).json()
        gainers = sorted(top_m + watch_m, key=lambda x: x.get('price_change_percentage_24h') or 0, reverse=True)[:5]
        return top_m, watch_m, gainers
    except: return [], [], []

def send_telegram(text):
    requests.post(f"https://api.telegram.org{TOKEN}/sendMessage", 
                  data={'chat_id': CHANNEL_ID, 'text': text, 'parse_mode': 'Markdown'})

def format_line(c):
    name, price = c['symbol'].upper(), c['current_price']
    change = c.get('price_change_percentage_24h') or 0
    emoji = "🟢" if change > 0 else "🔴"
    p_str = f"{price:,}" if price >= 1 else f"{price:.7f}".rstrip('0')
    return f"{emoji} {name}: `${p_str}` ({change:+.1f}%)\n"

print("ربات فعال شد...")
while True:
    top_m, watch_m, top_g = get_crypto_data()
    if top_m:
        tether = get_tether_price()
        # پیام ۱: سربرگ و پامپی‌ها
        m1 = f"🚀 **گزارش بازار**\n⏰ {time.strftime('%H:%M')}\n💵 تتر: `{tether:,}` ت\n\n🔥 **۵ پامپ برتر:**\n"
        for g in top_g: m1 += f" ├ {g['symbol'].upper()}: {g['price_change_percentage_24h']:+.1f}%\n"
        send_telegram(m1)
        time.sleep(2)
        # پیام ۲: برترین‌های مارکت
        m2 = "🔝 **۲۰ ارز اول بازار:**\n\n"
        for c in top_m: m2 += format_line(c)
        send_telegram(m2)
        time.sleep(2)
        # پیام ۳: لیست شما
        m3 = "⭐ **لیست اختصاصی شما:**\n\n"
        for c in watch_m: m3 += format_line(c)
        m3 += "\n🔄 آپدیت: ۶۰ ثانیه دیگر"
        send_telegram(m3)
    time.sleep(60)
