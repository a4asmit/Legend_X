"""



telegram_bot.py
---------------
Legend_X Telegram Bot with Real Telegram Integration

Commands:
  /start - Show menu
  /news <count> - Read latest news (shuffled)
  /feargreed - Current market Fear & Greed Index
  /gainers - Top 10 gaining coins (24H)
  /losers - Top 10 losing coins (24H)
  /volume - Top 10 coins by trading volume (24H)
  /trend <symbol> - 6-Factor TA Trend Detector (e.g. /trend BTC)

Usage:
    python telegram_bot.py
"""
import csv
import time
import json
import os
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import urllib.request
# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Import telegram library
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[WARNING] python-telegram-bot not installed. Run: pip install python-telegram-bot")


class LegendXBot:
    """Legend_X Telegram Bot Handler"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.news_dir = self.data_dir / "news"  
    
    def load_news(self):
        """Load latest news from data/news/news_latest.json"""
        news_file = self.news_dir / "news_latest.json"
        if not news_file.exists():
            return None
        try:
            with open(news_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def cmd_start(self):
        """Handle /start command"""
        message = """
╔════════════════════════════════════╗
║       LEGEND_X BOT MENU            ║
╚════════════════════════════════════╝

[*] <b>Available Commands:</b>

/start - Show menu
/news &lt;count&gt; - Read latest news (e.g. /news 5)
/feargreed - Current market Fear &amp; Greed Index
/gainers - Top 10 gaining coins (24H)
/losers - Top 10 losing coins (24H)
/fgainers - Top 10 filtered gainers (All exchanges, No scam tokens)
/volume - Top 10 coins by trading volume (24H)
/trend &lt;symbol&gt; - 6-Factor TA Trend Detector
/liquidation &lt;symbol&gt; - Leverage trap detector (default: BTC)
/map &lt;symbol&gt; - Visual liquidity heatmap (default: BTC)
/flow &lt;symbol&gt; - Order flow &amp; CVD trap detector (default: BTC)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[!] <b>How it works:</b>
- Fetches latest crypto news articles
- Shuffles them for a fresh view every time
- Uses pure math for Technical Analysis (No lagging libraries)

[STATUS] <b>Current Status:</b> [OK] OPERATIONAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return message

    def cmd_news(self, count=5):
        """Handle /news command. Fetches 'count' randomized articles"""
        news_data = self.load_news()
        if not news_data:
            return "[ERROR] No news data found. Make sure <code>data/news/news_latest.json</code> exists."
        
        if isinstance(news_data, list):
            articles = news_data
        elif isinstance(news_data, dict):
            articles = news_data.get('news', news_data.get('articles', news_data.get('results', news_data.get('data', []))))
        else:
            return "[ERROR] Invalid news data format in JSON file."

        if not articles:
            return "[ERROR] No articles found in the news file."

        count = min(count, len(articles), 20) 
        random.shuffle(articles)
        
        message = f"[NEWS] <b>LATEST CRYPTO NEWS</b> <i>({count} of {len(articles)})</i>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for idx, article in enumerate(articles[:count], 1):
            title = article.get('title', article.get('headline', 'No Title'))
            message += f"\n<b>{idx}.</b>  {title}\n"
                
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return message

    def cmd_feargreed(self):
        """Handle /feargreed command - Fetches current Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            fng_data = data['data'][0]
            value = int(fng_data['value'])
            classification = fng_data['value_classification'].capitalize()
            
            if value <= 25: indicator = "[EXTREME FEAR]"
            elif value <= 45: indicator = "[FEAR]"
            elif value <= 55: indicator = "[NEUTRAL]"
            elif value <= 75: indicator = "[GREED]"
            else: indicator = "[EXTREME GREED]"
            
            message = f"""
[INDEX] <b>CRYPTO FEAR &amp; GREED INDEX</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{indicator} <b>Current Score: {value} / 100</b>
&gt;&gt; Classification: <b>{classification}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[!] <b>Scale:</b>
0-24  -&gt; Extreme Fear
25-49 -&gt; Fear
50    -&gt; Neutral
51-74 -&gt; Greed
75-100 -&gt; Extreme Greed

[WARNING] <i>Buy when there's blood in the streets (Fear), 
be cautious when everyone is greedy.</i>
"""
            return message
        except Exception as e:
            return "[ERROR] Failed to fetch Fear & Greed Index. Please try again later."

    def cmd_gainers(self):
        return self._fetch_top_coins("gainers")

    def cmd_losers(self):
        return self._fetch_top_coins("losers")

    def _fetch_top_coins(self, coin_type):
        try:
            url = "https://fapi1.binance.com/fapi/v1/ticker/24hr"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
            
            usdt_pairs = [t for t in data if t['symbol'].endswith('USDT')]
            exclude_keywords = ['UPUSDT', 'DOWNUSDT', 'BULLUSDT', 'BEARUSDT', 'BUSDUSDT', 'USDCUSDT', 'TUSDUSDT', 'DAIUSDT', 'USDPUSDT']
            clean_pairs = [t for t in usdt_pairs if t['symbol'] not in exclude_keywords]
            
            sorted_pairs = sorted(clean_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
            
            if coin_type == "gainers":
                top_coins = sorted_pairs[:10]
                title = "TOP 10 GAINERS"
                indicator = "[UP]"
            else:
                top_coins = sorted_pairs[-10:][::-1]
                title = "TOP 10 LOSERS"
                indicator = "[DOWN]"
            
            message = f"[MARKET] <b>{title} (24H)</b>\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for idx, coin in enumerate(top_coins, 1):
                symbol = coin['symbol'].replace('USDT', '')
                price = float(coin['lastPrice'])
                change = float(coin['priceChangePercent'])
                volume = float(coin['quoteVolume'])
                
                if price < 0.01: price_str = f"${price:.6f}"
                elif price < 1: price_str = f"${price:.4f}"
                else: price_str = f"${price:,.2f}"
                
                if volume > 1_000_000_000: vol_str = f"${volume / 1_000_000_000:.2f}B"
                elif volume > 1_000_000: vol_str = f"${volume / 1_000_000:.2f}M"
                else: vol_str = f"${volume:,.0f}"
                    
                change_str = f"{change:+.2f}%"
                
                message += f"\n<b>{idx}.</b> {symbol}\n"
                message += f"   {indicator} Price: {price_str} | Change: {change_str} | Vol: {vol_str}\n"
            
            message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            return message
        except Exception as e:
            return "[ERROR] Failed to fetch market data. Please try again later."

    def cmd_volume(self):
        return self._fetch_top_volume()

    def _fetch_top_volume(self):
        try:
            url = "https://fapi1.binance.com/fapi/v1/ticker/24hr"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
            
            usdt_pairs = [t for t in data if t['symbol'].endswith('USDT')]
            exclude_keywords = ['UPUSDT', 'DOWNUSDT', 'BULLUSDT', 'BEARUSDT', 'BUSDUSDT', 'USDCUSDT', 'TUSDUSDT', 'DAIUSDT', 'USDPUSDT']
            clean_pairs = [t for t in usdt_pairs if t['symbol'] not in exclude_keywords]
            
            sorted_pairs = sorted(clean_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
            top_coins = sorted_pairs[:10]
            
            message = f"[MARKET] <b>TOP 10 VOLUME (24H)</b>\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for idx, coin in enumerate(top_coins, 1):
                symbol = coin['symbol'].replace('USDT', '')
                price = float(coin['lastPrice'])
                change = float(coin['priceChangePercent'])
                volume = float(coin['quoteVolume'])
                
                if price < 0.01: price_str = f"${price:.6f}"
                elif price < 1: price_str = f"${price:.4f}"
                else: price_str = f"${price:,.2f}"
                
                if volume > 1_000_000_000: vol_str = f"${volume / 1_000_000_000:.2f}B"
                elif volume > 1_000_000: vol_str = f"${volume / 1_000_000:.2f}M"
                else: vol_str = f"${volume:,.0f}"
                    
                change_str = f"{change:+.2f}%"
                
                message += f"\n<b>{idx}.</b> {symbol}\n"
                message += f"   [VOL] Price: {price_str} | Vol: {vol_str} | Change: {change_str}\n"
            
            message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            return message
        except Exception as e:
            return "[ERROR] Failed to fetch volume data. Please try again later."

    # ══════════════════════════════════════════════════════════════════════════════════
    # 6-FACTOR TREND DETECTOR
    # ══════════════════════════════════════════════════════════════════════════════════

    def cmd_trend(self, symbol):
        """Handle /trend command - 6 Factor Binance or 3 Factor CoinGecko"""
        base_symbol = symbol.upper().replace("/", "").replace("USDT", "")
        binance_symbol = base_symbol + "USDT"
        
        # --- ATTEMPT 1: BINANCE 6-FACTOR TA ---
        try:
            kline_url = f"https://fapi1.binance.com/fapi/v1/klines?symbol={binance_symbol}&interval=4h&limit=100"
            req = urllib.request.Request(kline_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                klines = json.loads(response.read().decode())
            
            if not klines or len(klines) < 50:
                raise ValueError("Not enough data") # Trigger CoinGecko fallback

            # Fetch Funding Rate
            funding_score = 0
            funding_val = 0.0
            try:
                fund_url = f"https://fapi1.binance.com/fapi/v1/premiumIndex?symbol={binance_symbol}"
                freq = urllib.request.Request(fund_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(freq, timeout=5) as response:
                    fund_data = json.loads(response.read().decode())
                funding_val = float(fund_data.get('lastFundingRate', 0))
                if funding_val > 0.05: funding_score = -2
                elif funding_val < -0.05: funding_score = 2
                else: funding_score = 0
            except:
                funding_val = None

            # Calculate Indicators
            try: structure_score = self._calc_structure(klines) or 0
            except: structure_score = 0
            try: adx_score, adx_val = self._calc_adx(klines) or (0, 0); adx_val = adx_val or 0
            except: adx_score, adx_val = 0, 0
            try: rsi_score, rsi_val = self._calc_rsi(klines) or (0, 0); rsi_val = rsi_val or 0
            except: rsi_score, rsi_val = 0, 0
            try: volume_score = self._calc_volume(klines) or 0
            except: volume_score = 0
            try: wick_score = self._calc_wick(klines[-1]) or 0
            except: wick_score = 0

            total_score = (structure_score * 2) + (adx_score * 2) + (funding_score * 2) + volume_score + rsi_score + wick_score

            if total_score >= 7: verdict = "[STRONG BULLISH]"
            elif total_score >= 2: verdict = "[BULLISH]"
            elif total_score <= -7: verdict = "[STRONG BEARISH]"
            elif total_score <= -2: verdict = "[BEARISH]"
            else: verdict = "[NEUTRAL]"

            current_price = float(klines[-1][4])
            if current_price < 0.01: price_str = f"${current_price:.6f}"
            elif current_price < 1: price_str = f"${current_price:.4f}"
            else: price_str = f"${current_price:,.2f}"

            fund_str = f"{funding_val*100:.3f}%" if funding_val is not None else "N/A (Spot Only)"

            def score_format(val, weight=1):
                actual = (val or 0) * weight
                if actual > 0: return f"[UP] +{actual}"
                elif actual < 0: return f"[DOWN] {actual}"
                else: return f"[NEUTRAL] {actual}"

            if total_score >= 7:
                summary = "[STRONG BULLISH]: All factors aligned. High confidence uptrend with muscle.\nAction: Look for long entries. Standard to aggressive position sizing is acceptable."
            elif total_score >= 2:
                summary = "[BULLISH]: Uptrend is present, but some factors lack full confirmation (e.g., low volume or overextended RSI).\nAction: Look for longs, but use smaller position sizes and keep stop-losses tight."
            elif total_score <= -7:
                summary = "[STRONG BEARISH]: Heavy selling pressure and trend breakdown. High confidence downtrend.\nAction: Look for short entries. Standard to aggressive position sizing is acceptable."
            elif total_score <= -2:
                summary = "[BEARISH]: Downtrend is present, but some factors lack full confirmation.\nAction: Look for shorts, but use smaller position sizes and keep stop-losses tight."
            else:
                summary = "[NEUTRAL]: Market is choppy or transitioning. No clear edge. Conflicting signals between trend and momentum.\nAction: Stay out of swing trades. Preserve capital. Wait for a clear break above +2 or below -2."

            message = f"""
[TREND] <b>{base_symbol} COMPOSITE ANALYSIS</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Price: {price_str}
Verdict: <b>{verdict}</b> (Score: {total_score}/9)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ANALYSIS]
1. Market Structure (x2): {score_format(structure_score, 2)}
2. ADX Strength (x2):    {score_format(adx_score, 2)} (Value: {adx_val:.1f})
3. Funding Rate (x2):    {score_format(funding_score, 2)} (Rate: {fund_str})
4. RSI Momentum (x1):    {score_format(rsi_score)} (Value: {rsi_val:.1f})
5. Volume vs Avg (x1):   {score_format(volume_score)}
6. Wick Rejection (x1):  {score_format(wick_score)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SUMMARY]
{summary}

[SCALE GUIDE]
-9 to -7 : STRONG BEARISH -- High confidence short
-6 to -2 : BEARISH        -- Cautious short
-1 to +1 : NEUTRAL        -- Stay out / Choppy market
+2 to +6 : BULLISH        -- Cautious long
+7 to +9 : STRONG BULLISH -- High confidence long
"""
            return message

        except (urllib.error.HTTPError, ValueError):
            # --- ATTEMPT 2: COINGECKO 3-FACTOR MACRO TREND ---
            try:
                search_url = f"https://api.coingecko.com/api/v3/search?query={base_symbol}"
                req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    search_data = json.loads(response.read().decode())
                
                coin_id = None
                for coin in search_data.get('coins', []):
                    if coin.get('symbol', '').upper() == base_symbol:
                        coin_id = coin.get('id')
                        break
                
                if not coin_id:
                    return f"[ERROR] Symbol {base_symbol} not found on Binance or CoinGecko."

                market_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}&sparkline=false"
                req = urllib.request.Request(market_url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    market_data = json.loads(response.read().decode())
                
                if not market_data: return f"[ERROR] No market data for {base_symbol}."
                
                data = market_data[0]
                price = data.get('current_price', 0)
                change_24h = data.get('price_change_percentage_24h', 0) or 0
                change_7d = data.get('price_change_percentage_7d', 0) or 0
                mcap = data.get('market_cap', 0) or 0
                vol = data.get('total_volume', 0) or 0
                
                # Calculate 3-Factor Macro Score
                if change_24h > 5: score_24h = 2
                elif change_24h > 0: score_24h = 1
                elif change_24h < -5: score_24h = -2
                elif change_24h < 0: score_24h = -1
                else: score_24h = 0
                
                if change_7d > 10: score_7d = 2
                elif change_7d > 0: score_7d = 1
                elif change_7d < -10: score_7d = -2
                elif change_7d < 0: score_7d = -1
                else: score_7d = 0
                
                vol_ratio = (vol / mcap * 100) if mcap > 0 else 0
                if vol_ratio > 10: score_vol = 1
                elif vol_ratio < 2: score_vol = -1
                else: score_vol = 0
                
                total_score = score_24h + score_7d + score_vol
                
                if total_score >= 3: verdict = "[STRONG BULLISH]"
                elif total_score >= 1: verdict = "[BULLISH]"
                elif total_score <= -3: verdict = "[STRONG BEARISH]"
                elif total_score <= -1: verdict = "[BEARISH]"
                else: verdict = "[NEUTRAL]"
                
                if price < 0.01: price_str = f"${price:.6f}"
                elif price < 1: price_str = f"${price:.4f}"
                else: price_str = f"${price:,.2f}"
                
                if mcap > 1_000_000_000: mcap_str = f"${mcap / 1_000_000_000:.2f}B"
                elif mcap > 1_000_000: mcap_str = f"${mcap / 1_000_000:.2f}M"
                else: mcap_str = f"${mcap:,.0f}"

                # --- GENERATE ACTIONABLE SUMMARY (COINGECKO) ---
                if total_score >= 3:
                    summary = "[STRONG BULLISH]: Strong macro momentum across multiple timeframes with high market interest.\nAction: Look for long entries. The broader trend is heavily in your favor."
                elif total_score >= 1:
                    summary = "[BULLISH]: Positive macro momentum, but may be lacking volume confirmation or shorter-term strength.\nAction: Look for longs, but keep position sizes small and wait for dips."
                elif total_score <= -3:
                    summary = "[STRONG BEARISH]: Heavy macro selling pressure across timeframes.\nAction: Look for short entries. The broader trend is strongly against longs."
                elif total_score <= -1:
                    summary = "[BEARISH]: Negative macro momentum, but lacking strong volume confirmation.\nAction: Look for shorts, but keep position sizes small and wait for relief pumps to short."
                else:
                    summary = "[NEUTRAL]: Macro trend is flat or conflicting. No clear edge currently.\nAction: Stay out of swing trades. Preserve capital until a clear trend emerges."

                message = f"""
[TREND] <b>{base_symbol} MACRO ANALYSIS</b>
<i>Source: CoinGecko (Not on Binance)</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Price: {price_str}
Market Cap: {mcap_str}
Verdict: <b>{verdict}</b> (Score: {total_score}/5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[MACRO ANALYSIS]
1. 24h Momentum:   {score_24h:+d} ({change_24h:+.2f}%)
2. 7d Momentum:    {score_7d:+d} ({change_7d:+.2f}%)
3. Volume Activity: {score_vol:+d} (Vol/MCap: {vol_ratio:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SUMMARY]
{summary}

[SCALE GUIDE]
-5 to -3 : STRONG BEARISH -- High confidence short
-2 to -1 : BEARISH        -- Cautious short
0        : NEUTRAL        -- Stay out / Choppy market
+1 to +2 : BULLISH        -- Cautious long
+3 to +5 : STRONG BULLISH -- High confidence long
"""
                return message

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    return "[ERROR] CoinGecko rate limit hit. Wait 60s."
                return f"[ERROR] Symbol {base_symbol} not found."
            except Exception as e:
                return f"[ERROR] Failed to analyze {base_symbol}. {str(e)}"
        
        except Exception as e:
            return f"[ERROR] Failed to analyze {base_symbol}. {str(e)}"

    # --- Pure Python Math Helpers ---

    def _calc_structure(self, klines):
        """Factor 1: Market Structure (HH/HL)"""
        highs = [float(k[2]) for k in klines[-50:]]
        lows = [float(k[3]) for k in klines[-50:]]
        
        peaks = []
        troughs = []
        for i in range(1, len(highs)-1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]: peaks.append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]: troughs.append(lows[i])
            
        if len(peaks) >= 2 and len(troughs) >= 2:
            hh = peaks[-1] > peaks[-2]
            hl = troughs[-1] > troughs[-2]
            lh = peaks[-1] < peaks[-2]
            ll = troughs[-1] < troughs[-2]
            
            if hh and hl: return 1  # Bullish
            if lh and ll: return -1 # Bearish
        return 0

    def _calc_adx(self, klines, period=14):
        """Factor 2: ADX (Trend Muscle)"""
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        
        tr, plus_dm, minus_dm = [], [], []
        for i in range(1, len(klines)):
            h, l, c = highs[i], lows[i], closes[i-1]
            ph, pl = highs[i-1], lows[i-1]
            
            tr_val = max(h - l, abs(h - c), abs(l - c))
            plus_dm_val = max(0, h - ph) if h - ph > pl - l else 0
            minus_dm_val = max(0, pl - l) if pl - l > h - ph else 0
            
            tr.append(tr_val)
            plus_dm.append(plus_dm_val)
            minus_dm.append(minus_dm_val)
            
        atr = [sum(tr[:period]) / period]
        s_plus_dm = [sum(plus_dm[:period])]
        s_minus_dm = [sum(minus_dm[:period])]
        
        for i in range(period, len(tr)):
            atr.append((atr[-1] * (period - 1) + tr[i]) / period)
            s_plus_dm.append((s_plus_dm[-1] * (period - 1) + plus_dm[i]) / period)
            s_minus_dm.append((s_minus_dm[-1] * (period - 1) + minus_dm[i]) / period)
            
        dx_list = []
        for i in range(len(atr)):
            plus_di = (s_plus_dm[i] / atr[i]) * 100 if atr[i] else 0
            minus_di = (s_minus_dm[i] / atr[i]) * 100 if atr[i] else 0
            di_sum = plus_di + minus_di
            dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum else 0
            dx_list.append(dx)
            
        if len(dx_list) < period: return 0, 0
        adx = sum(dx_list[:period]) / period
        for i in range(period, len(dx_list)):
            adx = (adx * (period - 1) + dx_list[i]) / period
            
        if adx > 25: return 1, adx   # Strong trend
        if adx < 20: return -1, adx  # Choppy/Weak
        return 0, adx                # Moderate

    def _calc_rsi(self, klines, period=14):
        """Factor 5: RSI (Exhaustion/Momentum)"""
        closes = [float(k[4]) for k in klines]
        gains, losses = [], []
        
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))
            
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        if avg_loss == 0: rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
        if 50 < rsi < 70: return 1, rsi     # Healthy bull momentum
        elif 30 < rsi < 50: return -1, rsi   # Bear momentum
        else: return 0, rsi                  # Overextended or flat

    def _calc_volume(self, klines):
        """Factor 4: Volume vs 20-period average"""
        vols = [float(k[5]) for k in klines[-30:]]
        if len(vols) < 20: return 0
        
        current_vol = vols[-1]
        avg_vol = sum(vols[-21:-1]) / 20
        
        if current_vol > avg_vol * 1.5: return 1   # High volume
        elif current_vol < avg_vol * 0.5: return -1 # Low volume
        return 0

    def _calc_wick(self, kline):
        """Factor 6: Wick Rejection (PA Entry)"""
        o, h, l, c = float(kline[1]), float(kline[2]), float(kline[3]), float(kline[4])
        body = abs(c - o)
        if body == 0: body = 0.0000001 
        
        lower_wick = min(o, c) - l
        upper_wick = h - max(o, c)
        
        if c > o: # Green candle
            if lower_wick > body * 2: return 1 # Buyers rejecting lower prices
        else:     # Red candle
            if upper_wick > body * 2: return -1 # Sellers rejecting higher prices
        return 
    
    def cmd_liquidation(self, symbol="BTC"):
        """Handle /liquidation command - Binance Leverage Trap Detector"""
        symbol = symbol.upper().replace("/", "").replace("USDT", "")
        pair = symbol + "USDT"
        
        try:
            # 1. Fetch Open Interest
            try:
                oi_url = f"https://fapi1.binance.com/fapi/v1/openInterest?symbol={pair}"
                req_oi = urllib.request.Request(oi_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_oi, timeout=10) as response:
                    oi_data = json.loads(response.read().decode())
                open_interest = float(oi_data['openInterest'])
            except Exception as e:
                return f"[ERROR] Failed to fetch Open Interest: {str(e)}"

            # 2. Fetch Current Price (Futures Mark Price - Safer than Spot for this)
            try:
                price_url = f"https://fapi1.binance.com/fapi/v1/ticker/price?symbol={pair}"
                req_price = urllib.request.Request(price_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_price, timeout=10) as response:
                    price_data = json.loads(response.read().decode())
                current_price = float(price_data['price'])
            except Exception as e:
                return f"[ERROR] Failed to fetch Price: {str(e)}"
            
            oi_usd = open_interest * current_price
            
            # 3. Fetch Top Trader Long/Short Ratio (Accounts)
            try:
                ls_url = f"https://fapi1.binance.com/futures/data/topLongShortAccountRatio?symbol={pair}&period=5m&limit=1"
                req_ls = urllib.request.Request(ls_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_ls, timeout=10) as response:
                    ls_data = json.loads(response.read().decode())
                
                long_pct = float(ls_data[0]['longAccount']) * 100
                short_pct = float(ls_data[0]['shortAccount']) * 100
            except Exception as e:
                return f"[ERROR] Failed to fetch Long/Short Ratio: {str(e)}"
            
            # 4. Fetch Funding Rate
            try:
                fund_url = f"https://fapi1.binance.com/fapi/v1/premiumIndex?symbol={pair}"
                req_fund = urllib.request.Request(fund_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_fund, timeout=10) as response:
                    fund_data = json.loads(response.read().decode())
                funding_rate = float(fund_data.get('lastFundingRate', 0))
            except:
                funding_rate = 0.0

            # --- Format Numbers ---
            if oi_usd > 1_000_000_000: oi_str = f"${oi_usd / 1_000_000_000:.2f}B"
            elif oi_usd > 1_000_000: oi_str = f"${oi_usd / 1_000_000:.2f}M"
            else: oi_str = f"${oi_usd:,.0f}"
            
            fund_str = f"{funding_rate*100:.3f}%"
            
            # --- Determine Trap/Squeeze Setup ---
            if long_pct > 60 and funding_rate > 0.01:
                trap = "[LONG SQUEEZE RISK] - Market overleveraged Long. Vulnerable to a price drop."
            elif short_pct > 60 and funding_rate < -0.01:
                trap = "[SHORT SQUEEZE RISK] - Market overleveraged Short. Vulnerable to a price pump."
            elif long_pct > 55:
                trap = "[LONG BIAS] - Slightly more longs, but no extreme squeeze setup yet."
            elif short_pct > 55:
                trap = "[SHORT BIAS] - Slightly more shorts, but no extreme squeeze setup yet."
            else:
                trap = "[BALANCED] - No extreme leverage trap detected."

            message = f"""
[LIQUIDATION] <b>{symbol} LEVERAGE TRAP DETECTOR</b>
<i>Source: Binance Futures</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[LEVERAGE EXPOSURE]
Open Interest: <b>{oi_str}</b> ({open_interest:,.2f} {symbol})
Current Price: ${current_price:,.2f}

[WHO IS TRAPPED?]
Top Trader Longs:  {long_pct:.1f}%
Top Trader Shorts: {short_pct:.1f}%

[FUNDING COST]
Funding Rate: {fund_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[VERDICT]
{trap}

[!] Open Interest = Total borrowed money. High OI + Skewed Ratio = Squeeze incoming.
"""
            return message

        except urllib.error.HTTPError:
            return f"[ERROR] Symbol {symbol} not found on Binance Futures."
        except Exception as e:
            return f"[ERROR] Failed to fetch leverage data. Details: {str(e)}"
        
    def cmd_map(self, symbol="BTC"):
        """Handle /map command - Text-based Macro Liquidity Levels"""
        symbol = symbol.upper().replace("/", "").replace("USDT", "")
        pair = symbol + "USDT"
        
        try:
            # 1. Fetch deep Order Book
            depth_url = f"https://fapi1.binance.com/fapi/v1/depth?symbol={pair}&limit=1000"
            req = urllib.request.Request(depth_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                depth_data = json.loads(response.read().decode())
            
            bids = depth_data.get('bids', [])
            asks = depth_data.get('asks', [])
            
            if not bids or not asks:
                return "[ERROR] Not enough order book data for this symbol."

            current_price = float(bids[0][0])
            
            # 2. Find actual range of the data we received
            actual_min = float(bids[-1][0])
            actual_max = float(asks[-1][0])
            actual_range = actual_max - actual_min
            
            # 3. Adaptive Step Size (Aim for ~15-20 rows of text)
            raw_step = actual_range / 15
            
            # Round step to a nice clean number (10, 50, 100, 500, 1000, 5000)
            nice_steps = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000]
            step = min(nice_steps, key=lambda x: abs(x - raw_step))
            
            min_price = int(actual_min / step) * step
            max_price = (int(actual_max / step) + 1) * step
            
            # 4. Create Macro Buckets
            num_buckets = int((max_price - min_price) / step) + 1
            start_bucket = int(min_price / step) * step
            
            buckets = {}
            for i in range(num_buckets):
                b_price = start_bucket + (i * step)
                buckets[b_price] = {'buy_vol': 0.0, 'sell_vol': 0.0}
                
            # 5. Populate Buckets
            for price, qty in bids:
                p, q = float(price), float(qty)
                b = int(p / step) * step
                if b in buckets: buckets[b]['buy_vol'] += (p * q)
                    
            for price, qty in asks:
                p, q = float(price), float(qty)
                b = int(p / step) * step
                if b in buckets: buckets[b]['sell_vol'] += (p * q)
            
            # 6. Format Text Output
            def fmt_vol(vol):
                if vol > 1_000_000_000: return f"${vol / 1_000_000_000:.1f}B"
                elif vol > 1_000_000: return f"${vol / 1_000_000:.1f}M"
                elif vol > 1_000: return f"${vol / 1_000:.0f}K"
                else: return "$0"

            text_lines = []
            sorted_keys = sorted(buckets.keys(), reverse=True)
            current_bucket = int(current_price / step) * step
            
            for b in sorted_keys:
                buy_v = buckets[b]['buy_vol']
                sell_v = buckets[b]['sell_vol']
                
                # Only show lines with meaningful volume or the current price line
                if buy_v > 1000 or sell_v > 1000 or b == current_bucket:
                    
                    # Format price label cleanly
                    if step >= 1000: price_label = f"{b/1000:.0f}K"
                    elif step >= 1: price_label = f"${b:,.0f}"
                    else: price_label = f"${b:,.2f}"
                    
                    marker = " &lt;&lt;&lt;" if b == current_bucket else ""
                    
                    # Construct line based on position relative to current price
                    if b > current_bucket:
                        # Above current price = Sell Resistance (Shorts)
                        if sell_v > 1000:
                            sell_str = f"Shorts: {fmt_vol(sell_v)}"
                            text_lines.append(f"{price_label}: {sell_str}{marker}")
                    elif b < current_bucket:
                        # Below current price = Buy Support (Longs)
                        if buy_v > 1000:
                            buy_str = f"Longs: {fmt_vol(buy_v)}"
                            text_lines.append(f"{price_label}: {buy_str}{marker}")
                    else:
                        # At current price line, show both if they exist
                        buy_str = f"Longs: {fmt_vol(buy_v)}" if buy_v > 1000 else "Longs: -"
                        sell_str = f"Shorts: {fmt_vol(sell_v)}" if sell_v > 1000 else "Shorts: -"
                        text_lines.append(f"{price_label}: {sell_str} | {buy_str}{marker}")
            
            text_summary = "\n".join(text_lines)
            
            # Show actual range covered in the header
            range_label = f"${actual_min:,.0f} - ${actual_max:,.0f}"

            message = f"""
[MAP] <b>{symbol} LIQUIDITY LEVELS</b>
<i>Shorts = Sell Resistance | Longs = Buy Support</i>
<i>Range: {range_label} (Step: ${step:,.0f})</i>

{text_summary}
"""
            return message

        except urllib.error.HTTPError:
            return f"[ERROR] Symbol {symbol} not found on Binance."
        except Exception as e:
            return f"[ERROR] Failed to generate map. {str(e)}"
        
    def cmd_fgainers(self):
        """Handle /fgainers command - Top filtered gaining coins across all exchanges"""
        try:
            # Fetch top 250 coins by Market Cap (ignores scam micro-caps automatically)
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
            
            # Apply Liquidity Filter first
            filtered_coins = []
            for coin in data:
                mcap = coin.get('market_cap', 0) or 0
                vol = coin.get('total_volume', 0) or 0
                
                # Must have at least $1M Market Cap and $100K Volume
                if mcap > 1_000_000 and vol > 100_000:
                    filtered_coins.append(coin)
            
            # NOW sort the filtered list by 24h price change (highest to lowest)
            filtered_coins.sort(key=lambda x: x.get('price_change_percentage_24h') or 0, reverse=True)
            
            # Take the top 10
            top_coins = filtered_coins[:10]
            
            if not top_coins:
                return "[ERROR] No legitimate gainers found meeting liquidity criteria."

            message = f"[MARKET] <b>TOP 10 FILTERED GAINERS (ALL EXCHANGES)</b>\n"
            message += "<i>Filtered: Top 250 MCap | Vol &gt; $100K</i>\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for idx, coin in enumerate(top_coins, 1):
                symbol = coin.get('symbol', 'N/A').upper()
                name = coin.get('name', 'N/A')
                price = coin.get('current_price', 0)
                change = coin.get('price_change_percentage_24h', 0) or 0
                mcap = coin.get('market_cap', 0)
                vol = coin.get('total_volume', 0)
                
                # Format Price
                if price is None: price = 0
                if price < 0.01: price_str = f"${price:.6f}"
                elif price < 1: price_str = f"${price:.4f}"
                else: price_str = f"${price:,.2f}"
                
                # Format Market Cap
                if mcap > 1_000_000_000: mcap_str = f"${mcap / 1_000_000_000:.2f}B"
                elif mcap > 1_000_000: mcap_str = f"${mcap / 1_000_000:.2f}M"
                else: mcap_str = f"${mcap:,.0f}"
                
                # Format Volume
                if vol > 1_000_000_000: vol_str = f"${vol / 1_000_000_000:.2f}B"
                elif vol > 1_000_000: vol_str = f"${vol / 1_000_000:.2f}M"
                else: vol_str = f"${vol:,.0f}"
                
                change_str = f"{change:+.2f}%"
                
                message += f"\n<b>{idx}.</b> {name} ({symbol})\n"
                message += f"   [UP] Price: {price_str} | Change: {change_str}\n"
                message += f"   [DATA] MCap: {mcap_str} | Vol: {vol_str}\n"
            
            message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            return message
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return "[ERROR] CoinGecko API rate limit hit. Please wait 60 seconds and try again."
            return f"[ERROR] API Error: {e.code}"
        except Exception as e:
            return "[ERROR] Failed to fetch filtered gainers. Please try again later."

    def cmd_flow(self, symbol="BTC"):
        """Handle /flow command - 12H Macro Order Flow and CVD"""
        symbol = symbol.upper().replace("/", "").replace("USDT", "")
        pair = symbol + "USDT"
        
        try:
            # 1. Fetch 12 Hours of 1-Minute Klines (720 candles)
            kline_url = f"https://fapi1.binance.com/fapi/v1/klines?symbol={pair}&interval=1m&limit=720"
            req = urllib.request.Request(kline_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                klines = json.loads(response.read().decode())
            
            if not klines or len(klines) < 60:
                return f"[ERROR] Not enough data for {symbol}."

            # 2. Calculate 12H Price Action
            open_price = float(klines[0][1])   # Open of 12h ago
            close_price = float(klines[-1][4]) # Current price
            price_change_pct = ((close_price - open_price) / open_price) * 100
            
            # 3. Calculate Taker Volume (The CVD Engine)
            taker_buy_vol = 0.0
            total_vol = 0.0
            
            for k in klines:
                # Index 7 = Total Volume (USD), Index 10 = Taker Buy Volume (USD)
                total_vol += float(k[7])
                taker_buy_vol += float(k[10])
                
            taker_sell_vol = total_vol - taker_buy_vol
            cvd_delta = taker_buy_vol - taker_sell_vol
            
            # Format Numbers
            def fmt_vol(vol):
                if vol > 1_000_000_000: return f"${vol / 1_000_000_000:.2f}B"
                elif vol > 1_000_000: return f"${vol / 1_000_000:.2f}M"
                elif vol > 1_000: return f"${vol / 1_000:.0f}K"
                else: return f"${vol:.0f}"
            
            buy_pct = (taker_buy_vol / total_vol * 100) if total_vol > 0 else 0
            sell_pct = (taker_sell_vol / total_vol * 100) if total_vol > 0 else 0
            
                       # 4. Divergence Logic (With 2% Threshold to filter out noise)
            price_up = close_price > open_price
            cvd_up = cvd_delta > 0
            
            # Calculate how skewed the CVD is (as a percentage of total volume)
            cvd_skew = (cvd_delta / total_vol * 100) if total_vol > 0 else 0
            
            if abs(cvd_skew) < 2:
                # CVD is too balanced (less than 2% skew) - No edge
                verdict = "[NEUTRAL] - Balanced Flow"
                explanation = "Aggressive buyers and sellers are perfectly balanced. No institutional dominance. Market is likely chopping or coiling."
            elif price_up and cvd_up and cvd_skew > 2:
                verdict = "[ACCUMULATION] - Healthy Bullish Flow"
                explanation = "Price is rising AND aggressive buyers are dominating over 12H. Institutional urgency is on the buy side. Trend is backed by real muscle."
            elif not price_up and not cvd_up and cvd_skew < -2:
                verdict = "[DISTRIBUTION] - Healthy Bearish Flow"
                explanation = "Price is falling AND aggressive sellers are dominating over 12H. Institutional urgency is on the sell side. Downward momentum is real."
            elif price_up and not cvd_up and cvd_skew < -2:
                verdict = "[BULL TRAP] - Fakeout / Distribution on Pump"
                explanation = "Price is rising over 12H, but aggressive sellers are heavily dominating. Whales are selling into the pump. This breakout lacks real buying muscle."
            elif not price_up and cvd_up and cvd_skew > 2:
                verdict = "[BEAR TRAP] - Absorption / Smart Money Buying"
                explanation = "Price is falling over 12H, but aggressive buyers are heavily dominating. Whales are absorbing the sell pressure. Dump may be a trap; reversal likely."
            else:
                verdict = "[NEUTRAL] - Mild Divergence"
                explanation = "Price and CVD are diverging slightly, but not enough volume to confirm a trap. Wait for clearer confirmation."

            message = f"""
[ORDER FLOW] <b>{symbol} CVD ANALYSIS (12H)</b>
<i>Source: Binance 1-Min Taker Volume</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[12H PRICE ACTION]
Price Change: {price_change_pct:+.2f}%

[TAKER FLOW (Last 12 Hours)]
Aggressive Buys:  {fmt_vol(taker_buy_vol)} ({buy_pct:.1f}%)
Aggressive Sells: {fmt_vol(taker_sell_vol)} ({sell_pct:.1f}%)
CVD Delta: <b>{fmt_vol(abs(cvd_delta))}</b> ({'Buyers Dominant' if cvd_delta > 0 else 'Sellers Dominant'})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[VERDICT]
{verdict}
{explanation}

[!] Scale: If Price & CVD diverge, follow the CVD. The aggressive money is the truth.
"""
            return message

        except urllib.error.HTTPError:
            return f"[ERROR] Symbol {symbol} not found on Binance."
        except Exception as e:
            return f"[ERROR] Failed to fetch order flow. {str(e)}"
    def collect_snapshot(self, symbol="BTC"):
        """Collects raw indicator data for logging to CSV"""
        symbol = symbol.upper().replace("/", "").replace("USDT", "")
        pair = symbol + "USDT"
        
        try:
            # 1. Fetch 4H Klines
            klines = self._fetch_api(f"https://fapi1.binance.com/fapi/v1/klines?symbol={pair}&interval=4h&limit=100")
            if not klines or len(klines) < 50: return None
            current_price = float(klines[-1][4])

            # 2. Funding Rate
            funding_score = 0
            funding_val = 0.0
            try:
                fund_data = self._fetch_api(f"https://fapi1.binance.com/fapi/v1/premiumIndex?symbol={pair}")
                funding_val = float(fund_data.get('lastFundingRate', 0))
                if funding_val > 0.05: funding_score = -2
                elif funding_val < -0.05: funding_score = 2
            except: pass

            # 3. Trend Math
            structure_score = self._calc_structure(klines) or 0
            adx_score, adx_val = self._calc_adx(klines) or (0, 0)
            rsi_score, rsi_val = self._calc_rsi(klines) or (0, 0)
            volume_score = self._calc_volume(klines) or 0
            wick_score = self._calc_wick(klines[-1]) or 0
            trend_total = (structure_score * 2) + (adx_score * 2) + (funding_score * 2) + volume_score + rsi_score + wick_score

            # 4. CVD Math
            cvd_skew = 0.0
            try:
                flow_klines = self._fetch_api(f"https://fapi1.binance.com/fapi/v1/klines?symbol={pair}&interval=1m&limit=720")
                taker_buy = sum(float(k[10]) for k in flow_klines)
                total_vol = sum(float(k[7]) for k in flow_klines)
                cvd_delta = taker_buy - (total_vol - taker_buy)
                cvd_skew = (cvd_delta / total_vol * 100) if total_vol > 0 else 0
            except: pass

            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol, 'price': current_price,
                'trend_score': trend_total, 'structure': structure_score,
                'adx': adx_score, 'funding': funding_score,
                'rsi': rsi_score, 'volume': volume_score,
                'wick': wick_score, 'cvd_skew': round(cvd_skew, 2),
                'funding_rate_pct': round(funding_val * 100, 3)
            }
        except Exception as e:
            print(f"[LOGGER] Snapshot Error: {str(e)}")
            return None
          
    def _fetch_api(self, url):
        """Helper to fetch API data with browser-like headers to bypass basic blocks"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'application/json,application/text',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read().decode('utf-8')
            if not data:
                raise ValueError("API returned empty response")
            return json.loads(data)
# ════════════════════════════════════════════════════════════════════════════════════════════════
# TELEGRAM COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = LegendXBot()
    message = bot.cmd_start()
    await update.message.reply_text(message, parse_mode='HTML')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = LegendXBot()
    count = 5
    if context.args:
        try:
            count = int(context.args[0])
            if count < 1: count = 1
            elif count > 20: count = 20
        except ValueError:
            await update.message.reply_text("[WARNING] Invalid number. Usage: <code>/news 5</code>", parse_mode='HTML')
            return
    message = bot.cmd_news(count=count)
    await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)

async def feargreed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = LegendXBot()
    message = bot.cmd_feargreed()
    await update.message.reply_text(message, parse_mode='HTML')

async def gainers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = LegendXBot()
    message = bot.cmd_gainers()
    await update.message.reply_text(message, parse_mode='HTML')

async def losers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = LegendXBot()
    message = bot.cmd_losers()
    await update.message.reply_text(message, parse_mode='HTML')

async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = LegendXBot()
    message = bot.cmd_volume()
    await update.message.reply_text(message, parse_mode='HTML')

async def trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trend command - requires a symbol argument"""
    if not context.args:
        await update.message.reply_text("[WARNING] Please provide a symbol. Usage: <code>/trend BTC</code>", parse_mode='HTML')
        return
    
    symbol = context.args[0]
    bot = LegendXBot()
    message = bot.cmd_trend(symbol)
    await update.message.reply_text(message, parse_mode='HTML')

async def liquidation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /liquidation command with optional symbol argument"""
    symbol = "BTC"  # Default to Bitcoin
    
    if context.args:
        symbol = context.args[0]
    
    bot = LegendXBot()
    message = bot.cmd_liquidation(symbol=symbol)
    await update.message.reply_text(message, parse_mode='HTML')

async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /map command - Sends text liquidity levels"""
    symbol = "BTC"  # Default
    
    if context.args:
        symbol = context.args[0]
    
    bot = LegendXBot()
    message = bot.cmd_map(symbol=symbol)
    await update.message.reply_text(message, parse_mode='HTML')

async def fgainers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fgainers command"""
    bot = LegendXBot()
    message = bot.cmd_fgainers()
    await update.message.reply_text(message, parse_mode='HTML')

async def flow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /flow command"""
    symbol = "BTC"  # Default
    
    if context.args:
        symbol = context.args[0]
    
    bot = LegendXBot()
    message = bot.cmd_flow(symbol=symbol)
    await update.message.reply_text(message, parse_mode='HTML')

async def log_market_data_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to log indicator data every 4 hours"""
    bot = LegendXBot()
    snapshot = bot.collect_snapshot(symbol="BTC")
    
    if not snapshot:
        print("[LOGGER] Failed to fetch data for CSV.")
        return
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_file = data_dir / "market_log.csv"
    
    # Check if file exists to write headers
    file_exists = csv_file.exists()
    
    with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=snapshot.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(snapshot)
        
    print(f"[LOGGER] Data saved to CSV at {snapshot['timestamp']}")

def main():
    """Start the Telegram bot using Webhooks"""
    
    if not TELEGRAM_AVAILABLE:
        print("[ERROR] python-telegram-bot not installed!")
        return
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERROR] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
        return
    
    # Required for Render free tier to wake the bot up
    PORT = int(os.environ.get('PORT', 5000))
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    
    if not WEBHOOK_URL:
        print("[ERROR] WEBHOOK_URL not set. Required for webhook mode.")
        print("Example: https://your-app-name.onrender.com")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("feargreed", feargreed_command))
    application.add_handler(CommandHandler("gainers", gainers_command))
    application.add_handler(CommandHandler("losers", losers_command))
    application.add_handler(CommandHandler("loosers", losers_command))
    application.add_handler(CommandHandler("volume", volume_command))
    application.add_handler(CommandHandler("trend", trend_command))
    application.add_handler(CommandHandler("liquidation", liquidation_command))
    application.add_handler(CommandHandler("map", map_command))
    application.add_handler(CommandHandler("fgainers", fgainers_command))
    application.add_handler(CommandHandler("flow", flow_command))

    # --- ADD BACKGROUND LOGGER JOB ---
    job_queue = application.job_queue
    # Run every 14400 seconds (4 hours), first run 60 seconds after boot
    job_queue.run_repeating(log_market_data_job, interval=14400, first=60)
  
    # Start polling
    print("\n" + "="*100)
    print("LEGEND_X TELEGRAM BOT - WEBHOOK MODE")
    print("="*100)
    print(f"\n✅ Bot started! Listening on port {PORT}...")
    print(f"🔗 Webhook URL: {WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}")
    print("\n" + "="*100 + "\n")
    
    # Run webhook instead of polling
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )


if __name__ == "__main__":
    if not TELEGRAM_AVAILABLE:
        print("\n[ERROR] python-telegram-bot library not found!")
        print("Install: pip install python-telegram-bot\n")
    else:
        main()
