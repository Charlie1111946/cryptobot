import os
import pandas as pd
import numpy as np
import requests
import time
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración del bot de Telegram
bot_token = "7755639693:AAEczAipCxprMLAzUE2L36AKy7S33wOdV_c"
chat_id = "5827231867"

bot = Bot(token=bot_token)
running = False  # Controla si el bot está activo
signal_found = False  # Evita spam de mensajes sin señal

def get_market_data():
    """
    Obtiene datos del mercado desde Binance.
    """
    try:
        url_binance = "https://api.binance.com/api/v3/ticker/price"
        symbols = ["BTCUSDT", "ETHUSDT"]
        response_binance = requests.get(url_binance).json()
        prices = {item['symbol']: float(item['price']) for item in response_binance if item['symbol'] in symbols}
        
        data = {
            'timestamp': [pd.Timestamp.now()],
            'BTC/USDT': [prices['BTCUSDT']],
            'ETH/USDT': [prices['ETHUSDT']]
        }
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error al obtener datos del mercado: {e}")
        return None

def calculate_indicators(df, pair):
    """
    Calcula RSI, MACD y Smart Money Concept (SMC).
    """
    # RSI
    delta = df[pair].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14, min_periods=1).mean()
    avg_loss = pd.Series(loss).rolling(window=14, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df[f'RSI_{pair}'] = 100 - (100 / (1 + rs))
    
    # MACD
    short_ema = df[pair].ewm(span=12, adjust=False).mean()
    long_ema = df[pair].ewm(span=26, adjust=False).mean()
    df[f'MACD_{pair}'] = short_ema - long_ema
    df[f'MACD_Signal_{pair}'] = df[f'MACD_{pair}'].ewm(span=9, adjust=False).mean()
    
    # Smart Money Concept (SMC)
    df[f'SMC_Structure_{pair}'] = np.where(df[f'MACD_{pair}'] > df[f'MACD_Signal_{pair}'], 'ALCISTA', 'BAJISTA')
    return df

def trading_strategy(df, pair):
    """
    Estrategia basada en RSI, MACD y SMC.
    """
    latest = df.iloc[-1]
    risk_reward_ratio = np.random.uniform(2, 5.5)
    signal = "SIN SEÑAL CLARA"
    take_profit = stop_loss = 0
    
    if latest[f'RSI_{pair}'] < 30 and latest[f'SMC_Structure_{pair}'] == 'ALCISTA':
        signal = "SEÑAL DE COMPRA"
        take_profit = latest[pair] * (1 + (risk_reward_ratio / 100))
        stop_loss = latest[pair] * (1 - (1 / risk_reward_ratio / 100))
    elif latest[f'RSI_{pair}'] > 70 and latest[f'SMC_Structure_{pair}'] == 'BAJISTA':
        signal = "SEÑAL DE VENTA"
        take_profit = latest[pair] * (1 - (risk_reward_ratio / 100))
        stop_loss = latest[pair] * (1 + (1 / risk_reward_ratio / 100))
    
    return signal, latest[pair], take_profit, stop_loss, round(risk_reward_ratio, 2)

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Envía señales de trading.
    """
    global running, signal_found
    
    if not running:
        await update.message.reply_text("El bot no está activo. Usa /start para iniciarlo.")
        return
    
    df = get_market_data()
    if df is None:
        await update.message.reply_text("⚠️ Error al obtener datos del mercado.")
        return
    
    df = calculate_indicators(df, 'BTC/USDT')
    df = calculate_indicators(df, 'ETH/USDT')
    
    btc_signal, btc_entry, btc_tp, btc_sl, btc_rr = trading_strategy(df, 'BTC/USDT')
    eth_signal, eth_entry, eth_tp, eth_sl, eth_rr = trading_strategy(df, 'ETH/USDT')
    
    if btc_signal == "SIN SEÑAL CLARA" and eth_signal == "SIN SEÑAL CLARA":
        if not signal_found:
            await bot.send_message(chat_id=chat_id, text="⏳ Analizando mercado... Esperando señales óptimas.")
            signal_found = True
        return
    
    message = f"📊 Señales de Trading:\n\n"
    message += f"🔹 **BTC/USDT**\n📍 Entrada: {btc_entry:.2f}\n🎯 TP: {btc_tp:.2f}\n🛑 SL: {btc_sl:.2f}\n📈 R/B: {btc_rr}:1\n📌 {btc_signal}\n\n"
    message += f"🔹 **ETH/USDT**\n📍 Entrada: {eth_entry:.2f}\n🎯 TP: {eth_tp:.2f}\n🛑 SL: {eth_sl:.2f}\n📈 R/B: {eth_rr}:1\n📌 {eth_signal}"
    
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    signal_found = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = True
    await bot.send_message(chat_id=chat_id, text="🤖 Bot ACTIVADO. Usa /signal para obtener señales y /stop para detenerlo.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = False
    await bot.send_message(chat_id=chat_id, text="⛔ Bot DETENIDO. Usa /start para reactivarlo.")

def main():
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("signal", send_signal))
    app.run_polling()

if __name__ == "__main__":
    main()









































































































    








