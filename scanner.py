import requests
import time
import sys
import os

# Hata çıktılarını engelle
sys.stderr = open(os.devnull, 'w')

# Telegram Bilgilerin
TELEGRAM_TOKEN = "8987497275:AAEylYkVvJrxCY41WkXz2pf68aKdWVRcTek"
CHAT_ID = "6126409933"

# Sanal Hesap ve Portföy Ayarları (Güncellendi)
TOTAL_CASH = 10500.0          # Başlangıç Kasa: 10.500 TL
MAX_ACTIVE_POSITIONS = 10     # Aynı anda maksimum 10 farklı coin slotu
ALLOCATION_PCT = 0.10         # Her pozisyon için kasanın %10'u (10 slota eşit dağılım)

ACTIVE_POSITIONS = []

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception:
        pass

def get_all_crypto_prices():
    # Binance'deki tüm USDT paritelerini dinamik olarak çeker
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        coins = {}
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                coins[symbol] = {
                    'price': float(item['lastPrice']),
                    'change_24h': float(item['priceChangePercent']),
                    'volume': float(item['quoteVolume'])
                }
        return coins
    except Exception:
        return {}

def run_crypto_10_slot_bot():
    global TOTAL_CASH, ACTIVE_POSITIONS
    
    print(f"[{time.strftime('%H:%M:%S')}] Tüm Binance kripto havuzu taranıyor...")
    market_data = get_all_crypto_prices()
    
    if not market_data:
        print("Fiyatlar alınamadı, sonraki tur bekleniyor.")
        return

    # 1. MEVCUT AÇIK POZİSYONLARI KONTROL ET (Kar Al: %3 / Zarar Kes: %2)
    updated_positions = []
    for pos in ACTIVE_POSITIONS:
        coin = pos['coin']
        entry_price = pos['entry_price']
        invested_tl = pos['invested_tl']
        
        if coin in market_data:
            current_price = market_data[coin]['price']
            profit_loss_pct = ((current_price - entry_price) / entry_price) * 100
            
            if profit_loss_pct >= 3.0 or profit_loss_pct <= -2.0:
                final_value = invested_tl * (1 + (profit_loss_pct / 100))
                profit_tl = final_value - invested_tl
                TOTAL_CASH += final_value  # Parayı kasaya geri ekle
                
                status_emoji = "🟢 KÂRLA KAPANDI" if profit_loss_pct > 0 else "🔴 ZARARLA KAPANDI"
                msg = (
                    f"🤖 *10 Slot Kripto Portföy - Satış Raporu*\n\n"
                    f"{status_emoji}\n"
                    f"🪙 *Coin:* `{coin}`\n"
                    f"💰 *Giriş:* `${entry_price:.4f}` | *Çıkış:* `${current_price:.4f}`\n"
                    f"📈 *Getiri:* `%%{profit_loss_pct:.2f}`\n"
                    f"💵 *Net Değişim:* `{profit_tl:+.2f} TL`\n"
                    f"🏦 *Güncel Toplam Kasa:* `{TOTAL_CASH:,.2f} TL`"
                )
                send_telegram(msg)
                print(f"Pozisyon Kapatıldı -> {coin} (%{profit_loss_pct:.2f})")
            else:
                updated_positions.append(pos)
        else:
            updated_positions.append(pos)
            
    ACTIVE_POSITIONS = updated_positions

    # 2. YENİ FIRSATLARI ARA VE BOŞ SLOTLARA (%10 BÜTÇEYLE) DAĞIT
    slots_available = MAX_ACTIVE_POSITIONS - len(ACTIVE_POSITIONS)
    
    if slots_available > 0 and TOTAL_CASH > 50:
        already_owned = [p['coin'] for p in ACTIVE_POSITIONS]
        
        # Hacmi yüksek (>2M USDT) ve o an yeşil yakan coinleri filtrele
        candidates = []
        for coin, info in market_data.items():
            if coin not in already_owned and info['volume'] > 2000000 and info['change_24h'] > 0.5:
                candidates.append((coin, info['change_24h'], info['price']))
                
        # En yüksek artış gösterene göre sırala
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        buys_to_make = min(slots_available, len(candidates))
        
        for i in range(buys_to_make):
            coin, change, price = candidates[i]
            budget_for_trade = TOTAL_CASH * ALLOCATION_PCT  # Kasanın %10'u
            
            if budget_for_trade < 20:
                continue
                
            TOTAL_CASH -= budget_for_trade
            
            new_pos = {
                'coin': coin,
                'entry_price': price,
                'invested_tl': budget_for_trade
            }
            ACTIVE_POSITIONS.append(new_pos)
            
            msg = (
                f"🤖 *10 Slot Kripto Portföy - Yeni Alım*\n\n"
                f"🚀 *Sepete Eklendi ({len(ACTIVE_POSITIONS)}/10):* `{coin}`\n"
                f"💰 *Giriş Fiyatı:* `${price:.4f}`\n"
                f"💼 *Ayrılan Tutar (%10):* `{budget_for_trade:,.2f} TL`\n"
                f"🎯 *Hedef:* `%3 Kâr / %2 Stop-Loss`"
            )
            send_telegram(msg)
            print(f"Yeni Pozisyon Açıldı -> {coin} ({budget_for_trade:.2f} TL)")
    else:
        print(f"Piyasa taranıyor. Aktif Slotlar: {len(ACTIVE_POSITIONS)}/{MAX_ACTIVE_POSITIONS} | Kasa: {TOTAL_CASH:,.2f} TL")

if __name__ == "__main__":
    print(f"10 Slotlu Kripto Portföy Botu Başlatıldı! Başlangıç Kasası: {TOTAL_CASH} TL\n")
    send_telegram("🤖 *10 Slotlu Kripto Portföy Botu Başlatıldı!*\n10.500 TL başlangıç kasası ile tüm Binance coinleri taranıyor, eşzamanlı 10'a kadar slot açılacak.")
    
    while True:
        run_crypto_10_slot_bot()
        time.sleep(300) # 5 dakikada bir tarama döngüsü