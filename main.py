import time
import requests
import os
import logging

# تنظیمات لاگ حرفه‌ای
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

WATCHLIST = ['grok-erc20', 'official-trump', 'dogecoin', 'pnut', 'solana', 'bitcoin']

def send_telegram(text):
    """ارسال پیام با فرمت HTML و مدیریت محدودیت سرعت تلگرام"""
    url = f"https://api.telegram.org{TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={'chat_id': CHANNEL_ID, 'text': text, 'parse_mode': 'HTML'}, timeout=25)
        if res.status_code == 429:
            wait = res.json().get('parameters', {}).get('retry_after', 15)
            time.sleep(wait)
            return send_telegram(text)
        return res.ok
    except Exception as e:
        logging.error(f"Telegram Error: {e}")
        return False

def get_market_data():
    """دریافت دیتای بازار در یک درخواست واحد برای صرفه‌جویی در API"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # ۱. قیمت تتر از نوبیتکس
        tether_val = "نوسانی"
        try:
            t_res = requests.get("https://api.nobitex.ir", timeout=15).json()
            if t_res.get('status') == 'ok':
                tether_val = f"{int(t_res['lastTradePrice']) // 10:,}"
        except: pass

        # ۲. دیتای کریپتو از کوین‌گکو
        top_ids = ['bitcoin', 'ethereum', 'binancecoin', 'solana', 'ripple', 'cardano', 'dogecoin', 'tron', 'polkadot', 'chainlink']
        all_ids = list(set(WATCHLIST + top_ids))
        
        cg_url = "https://api.coingecko.com"
        params = {'vs_currency': 'usd', 'ids': ','.join(all_ids), 'order': 'market_cap_desc'}
        
        response = requests.get(cg_url, params=params, headers=headers, timeout=30)
        if response.status_code == 429:
            logging.warning("CoinGecko Limit! Waiting...")
            time.sleep(45) # استراحت در صورت لیمیت شدن
            return None, None, None, tether_val

        data = response.json()
        if not isinstance(data, list): return None, None, None, tether_val

        top_20 = data[:20]
        watch_data = [c for c in data if c['id'] in WATCHLIST]
        gainers = sorted(data, key=lambda x: x.get('price_change_percentage_24h') or 0, reverse=True)[:5]
        
        return top_20, watch_data, gainers, tether_val
    except Exception as e:
        logging.error(f"Fetch Error: {e}")
        return None, None, None, "خطا"

def format_crypto(c):
    change = c.get('price_change_percentage_24h') or 0
    emoji = "🟢" if change > 0 else "🔴"
    price = c['current_price']
    p_str = f"{price:,}" if price >= 1 else f"{price:.8f}".rstrip('0')
    return f"{emoji} {c['symbol'].upper()}: <b>${p_str}</b> ({change:+.1f}%)\n"

if __name__ == "__main__":
    logging.info("Bot Started - Update Cycle: 60s")
    while True:
        try:
            top_20, watch, gainers, tether = get_market_data()
            if top_20:
                now = time.strftime('%H:%M')
                
                # ارسال پیام ۱
                m1 = f"🚀 <b>گزارش بازار</b>\n⏰ {now}\n💵 تتر: {tether} ت\n\n🔥 <b>برترین‌های صعودی:</b>\n"
                for g in gainers: m1 += f" ├ {g['symbol'].upper()}: {g['price_change_percentage_24h']:+.1f}%\n"
                send_telegram(m1)
                time.sleep(2)

                # ارسال پیام ۲
                m2 = "🔝 <b>۲۰ ارز اول بازار:</b>\n\n"
                for c in top_20: m2 += format_crypto(c)
                send_telegram(m2)
                time.sleep(2)

                # ارسال پیام ۳
                m3 = "⭐ <b>واچ‌لیست اختصاصی:</b>\n\n"
                for c in watch: m3 += format_crypto(c)
                m3 += f"\n🔄 <i>آپدیت بعدی: ۶۰ ثانیه دیگر</i>"
                send_telegram(m3)
            
            time.sleep(60) # سیکل ۶۰ ثانیه‌ای طبق درخواست شما
            
        except Exception as e:
            logging.critical(f"Loop Error: {e}")
            time.sleep(15)
