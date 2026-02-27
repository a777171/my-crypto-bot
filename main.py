import time
import requests
import os
import logging
from threading import Thread
from flask import Flask

# تنظیمات لاگ برای مشاهده وضعیت در کنسول Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- بخش وب‌سرور برای زنده نگه داشتن سرویس در پلن رایگان ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running! Monitoring market data..."

def run_web_server():
    # رندر پورت را از متغیر محیطی PORT می‌گیرد
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- دریافت متغیرهای محیطی (امنیت) ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WATCHLIST = ['grok-erc20', 'official-trump', 'dogecoin', 'pnut', 'solana', 'bitcoin']

def send_telegram(text):
    """ارسال پیام به تلگرام با استفاده از توکن و آیدی کانال از تنظیمات رندر"""
    if not TOKEN or not CHANNEL_ID:
        logging.error("BOT_TOKEN or CHANNEL_ID not found in Environment Variables!")
        return False
    
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
        all_ids = list(set(WATCHLIST + ['bitcoin', 'ethereum', 'solana', 'dogecoin']))
        cg_url = "https://api.coingecko.com"
        params = {'vs_currency': 'usd', 'ids': ','.join(all_ids), 'order': 'market_cap_desc'}
        
        response = requests.get(cg_url, params=params, headers=headers, timeout=30)
        if response.status_code == 429:
            logging.warning("CoinGecko Limit! Waiting 45s...")
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

def main_loop():
    logging.info("Main Loop Started - 60s intervals")
    while True:
        try:
            top_20, watch, gainers, tether = get_market_data()
            if top_20:
                now = time.strftime('%H:%M')
                
                # پیام ۱: خلاصه بازار و صعودی‌ها
                m1 = f"🚀 <b>گزارش بازار</b>\n⏰ {now}\n💵 تتر: {tether} ت\n\n🔥 <b>برترین‌های صعودی:</b>\n"
                for g in gainers: m1 += f" ├ {g['symbol'].upper()}: {g['price_change_percentage_24h']:+.1f}%\n"
                send_telegram(m1)
                
                time.sleep(2) # فاصله کوتاه بین پیام‌ها برای جلوگیری از بلاک تلگرام

                # پیام ۲: واچ‌لیست اختصاصی
                m2 = "⭐ <b>واچ‌لیست اختصاصی شما:</b>\n\n"
                for c in watch: m2 += format_crypto(c)
                m2 += f"\n🔄 <i>آپدیت بعدی: ۶۰ ثانیه دیگر</i>"
                send_telegram(m2)
            
            time.sleep(60) # سیکل ۶۰ ثانیه‌ای
            
        except Exception as e:
            logging.critical(f"Loop Error: {e}")
            time.sleep(20)

if __name__ == "__main__":
    # اجرای وب‌سرور در یک ترد (Thread) جداگانه
    Thread(target=run_web_server).start()
    # اجرای حلقه اصلی ربات
    main_loop()
