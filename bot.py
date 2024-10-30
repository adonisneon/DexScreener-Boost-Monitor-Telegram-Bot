import asyncio
from telegram import Bot
from telegram.constants import ParseMode  # Updated import
from telegram.ext import Application, CommandHandler
import requests
import json
from datetime import datetime
import logging
from typing import Set, Dict, Optional

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
CHAT_ID = "your-channel-id"
CHECK_INTERVAL = 60  # Seconds between checks (respect rate limit)

class DexScreenerBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.known_boosts: Set[str] = set()
        self.last_check_time = datetime.now()
        
    async def start(self) -> None:
        """Initialize the bot and start monitoring"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.monitor_boosts()

    async def cmd_start(self, update, context) -> None:
        await update.message.reply_text(
            "🚀 DexScreener Boost Monitor started!\n"
            "I'll notify you when new token boosts are detected.\n"
            "Use /status to check the monitoring status."
        )

    async def cmd_status(self, update, context) -> None:
        status_message = (
            "📊 Monitor Status:\n"
            f"Last check: {self.last_check_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Known boosts: {len(self.known_boosts)}\n"
            f"Check interval: {CHECK_INTERVAL} seconds"
        )
        await update.message.reply_text(status_message)

    def get_token_info(self, chain_id: str, token_address: str) -> Optional[Dict]:
        """Fetch detailed token information from DexScreener pairs API"""
        try:
            response = requests.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{token_address}",
                headers={},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('pairs') and len(data['pairs']) > 0:
                # Get the first pair as it usually contains the most relevant information
                pair = data['pairs'][0]
                return {
                    'name': pair['baseToken']['name'],
                    'symbol': pair['baseToken']['symbol'],
                    'market_cap': pair.get('marketCap', 0),
                    'fdv': pair.get('fdv', 0),
                    'price_usd': pair.get('priceUsd', '0'),
                    'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                    'info': pair.get('info', {})
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching token info: {e}")
            return None

    def format_social_links(self, info: Dict) -> str:
        """Format social media links from token info"""
        links = []
        
        # Add websites
        if 'websites' in info and info['websites']:
            for website in info['websites']:
                if website.get('url'):
                    links.append(f"🌐 [Website]({website['url']})")
        
        # Add social media
        if 'socials' in info and info['socials']:
            platform_icons = {
                'twitter': '🐦',
                'telegram': '📱',
                'discord': '💬',
                'medium': '📝',
                'github': '💻'
            }
            
            for social in info['socials']:
                platform = social.get('platform', '').lower()
                handle = social.get('handle', '')
                icon = platform_icons.get(platform, '🔗')
                
                if platform and handle:
                    if platform == 'twitter':
                        links.append(f"{icon} [Twitter](https://twitter.com/{handle})")
                    elif platform == 'telegram':
                        links.append(f"{icon} [Telegram](https://t.me/{handle})")
                    elif platform == 'discord':
                        links.append(f"{icon} [Discord]({handle})")
                    else:
                        links.append(f"{icon} [{platform.title()}]({handle})")
        
        return '\n'.join(links) if links else "No social links available"

    def format_number(self, num: float) -> str:
        """Format large numbers in a readable way"""
        if num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num / 1_000:.2f}K"
        return f"${num:.2f}"

    async def send_notification(self, boost_data: Dict) -> None:
        """Send a formatted notification about a new token boost"""
        token_info = self.get_token_info(boost_data['chainId'], boost_data['tokenAddress'])
        
        if token_info:
            message = (
                "🔥 *NEW TOKEN BOOST DETECTED* 🔥\n\n"
                f"*Token:* {token_info['name']} ({token_info['symbol']})\n"
                f"*Chain:* {boost_data['chainId']}\n"
                f"*Address:* `{boost_data['tokenAddress']}`\n\n"
                
                f"*💰 Token Metrics:*\n"
                f"• Market Cap: {self.format_number(token_info['market_cap'])}\n"
                f"• FDV: {self.format_number(token_info['fdv'])}\n"
                f"• Price: ${float(token_info['price_usd']):.8f}\n"
                f"• Liquidity: {self.format_number(token_info['liquidity_usd'])}\n\n"
                
                f"*🚀 Boost Details:*\n"
                f"• Boost Amount: {self.format_number(boost_data['amount'])}\n"
                f"• Total Amount: {self.format_number(boost_data['totalAmount'])}\n"
            )

            if boost_data.get('description'):
                message += f"\n*📝 Description:*\n{boost_data['description']}\n"

            message += f"\n*🔗 Important Links:*\n"
            if boost_data.get('url'):
                message += f"• [DexScreener]({boost_data['url']})\n"
            
            # Add social links
            if token_info.get('info'):
                message += "\n*Social Links:*\n"
                message += self.format_social_links(token_info['info'])

        else:
            # Fallback message if token info can't be retrieved
            message = (
                "🔥 *NEW TOKEN BOOST DETECTED* 🔥\n\n"
                f"*Chain:* {boost_data['chainId']}\n"
                f"*Token Address:* `{boost_data['tokenAddress']}`\n"
                f"*Boost Amount:* {self.format_number(boost_data['amount'])}\n"
                f"*Total Amount:* {self.format_number(boost_data['totalAmount'])}\n"
            )

        try:
            async with Bot(self.bot_token) as bot:
                await bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def get_latest_boosts(self) -> list:
        """Fetch the latest token boosts from DexScreener API"""
        try:
            response = requests.get(
                "https://api.dexscreener.com/token-boosts/latest/v1",
                headers={},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching boosts: {e}")
            return []

    async def monitor_boosts(self) -> None:
        """Main monitoring loop"""
        while True:
            try:
                latest_boosts = self.get_latest_boosts()
                
                if not isinstance(latest_boosts, list):
                    latest_boosts = [latest_boosts]

                for boost in latest_boosts:
                    boost_id = f"{boost['chainId']}_{boost['tokenAddress']}"
                    
                    if boost_id not in self.known_boosts:
                        self.known_boosts.add(boost_id)
                        await self.send_notification(boost)
                
                self.last_check_time = datetime.now()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(CHECK_INTERVAL)

async def main():
    """Main function to start the bot"""
    bot = DexScreenerBot(TELEGRAM_BOT_TOKEN, CHAT_ID)
    await bot.start()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
