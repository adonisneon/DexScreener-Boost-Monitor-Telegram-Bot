# DexScreener-Boost-Monitor-Telegram-Bot

A Telegram bot that automatically posts notifications to a Telegram channel when a token receives a boost on DexScreener. Users subscribe to the channel to receive updates, as the bot does not allow direct interaction for manual requests.

## Features

- Monitors DexScreener for new token boosts.
- Posts a notification with detailed information on each token boost, including token metrics, social links, and important links.
- Sends updates to a specified Telegram channel.
- Runs on an asynchronous loop for continuous monitoring with a configurable check interval.

## Setup

### Prerequisites
- Python 3.7 or higher
- Telegram Bot Token (from [BotFather](https://core.telegram.org/bots#botfather))
- Channel ID where the bot will post notifications

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adonisneon/DexScreener-Boost-Monitor-Telegram-Bot
   ```
2. **Install Dependencies: Install all required packages by running**:
    ```bash
    pip install -r requirements.txt
    ```
3. **Environment Configuration**:
   Set your bot token in the code:
   ```bash
   TOKEN = "your-telegram-bot-token"
   ```
   Replace CHAT_ID with your public channel link for automatic updates:
   ```bash
   CHAT_ID = "your-channel-id"
   ```
4. **Run the Bot**: Start the bot by executing:
   ```bash
   python bot.py
   ```

**Configuration**
CHECK_INTERVAL: Set the interval in seconds between checks. Default is 60 seconds.

**Contributing**
Pull requests are welcome. For major changes, please open an issue first to discuss your proposed changes.

**License**
This project is licensed under the MIT License.

