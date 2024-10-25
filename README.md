# BacBo-Signals

Automate your betting strategies with Selenium and Telegram notifications. This Python app lets you set predefined betting strategies and sends real-time signals to your Telegram channel, without aiming to predict or win money.

## Table of Contents

-   [Features](#features)
-   [Prerequisites](#prerequisites)
-   [Installation](#installation)
-   [Configuration](#configuration)
-   [Usage](#usage)
-   [Logging](#logging)
-   [Betting Strategy](#betting-strategy)
-   [Troubleshooting](#troubleshooting)
-   [Contributing](#contributing)
-   [License](#license)

## Features

-   **Automated Monitoring**: Continuously monitors betting results from a target website using Selenium WebDriver.
-   **Custom Betting Strategies**: Implements predefined betting patterns with support for gales (martingale strategy).
-   **Real-time Notifications**: Sends updates and alerts to your Telegram channel using a Telegram bot.
-   **Asynchronous Operations**: Utilizes `asyncio` for efficient asynchronous task handling.
-   **Error Handling & Logging**: Comprehensive logging of events and errors for easy troubleshooting.

## Prerequisites

-   **Website Account**: You will need an active account on the specified betting website for the script to function.
-   Python 3.7+
-   Google Chrome Browser
-   ChromeDriver: Ensure that the ChromeDriver version matches your installed Chrome browser version. [Download ChromeDriver](https://chromedriver.chromium.org/downloads)
-   Telegram Bot: Create a Telegram bot and obtain the bot token. [Creating a Telegram Bot](https://core.telegram.org/bots)
-   Telegram Channel: Create a Telegram channel and obtain the channel ID.

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/betting-strategy-automation.git
cd betting-strategy-automation
```

### Create a Virtual Environment (Optional but Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not provided, install the necessary packages manually:

```bash
pip install selenium python-dotenv python-telegram-bot
```

### Download ChromeDriver

Download the ChromeDriver executable that matches your Chrome browser version from [here](https://chromedriver.chromium.org/downloads).
Place the chromedriver executable in a directory that's in your system's PATH, or specify its path in the script.

## Configuration

### Create a .env File

In the root directory of the project, create a `.env` file and add the following variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_telegram_channel_id
```

-   `TELEGRAM_BOT_TOKEN`: The token you received from BotFather when creating your Telegram bot.
-   `TELEGRAM_CHANNEL_ID`: The unique identifier for your Telegram channel. You can obtain this by adding your bot to the channel and sending a message, then using the Telegram API to get updates.

### Set Up ChromeDriver Path (If Necessary)

If ChromeDriver is not in your system's PATH, modify the `webdriver.Chrome()` initialization in the script to include the executable path:

```python
driver = webdriver.Chrome(executable_path='/path/to/chromedriver')
```

## Usage

### Run the Script

```bash
python main.py
```

Replace `main.py` with the actual name of your Python script.

### Monitoring

The script will start monitoring the betting results from the specified website. Based on the predefined strategies, it will send notifications to your Telegram channel.

## Logging

-   **Log File**: All logs are stored in `logs.log` in the root directory.
-   **Log Details**: The log file includes timestamps, log levels, and detailed messages for each event and error.

## Betting Strategy

The `BettingStrategy` class implements the following strategies:

-   **Pattern Matching**: Detects specific patterns in the latest betting results to decide the next signal.
-   **Gale System**: If a signal fails, the script increases the signal frequency (gales) up to a maximum number to maintain consistency.

### Defined Strategies

-   Pattern: `['P', 'P', 'P']` → Signal: `'B'` (with up to 2 gales)
-   Pattern: `['B', 'B', 'B']` → Signal: `'P'` (with up to 2 gales)
-   Pattern: `['B', 'B', 'P']` → Signal: `'P'` (with up to 2 gales)
-   Pattern: `['P', 'P', 'B']` → Signal: `'B'` (with up to 2 gales)

You can modify or add strategies by editing the `strategies` list in the script.

## Troubleshooting

### ChromeDriver Issues

-   Ensure that the ChromeDriver version matches your installed Chrome browser version.
-   Verify that ChromeDriver is in your system's PATH or correctly specified in the script.

### Telegram Bot Errors

-   Double-check the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` in your `.env` file.
-   Ensure that the bot has the necessary permissions to post in the channel.

### Selenium Exceptions

-   The script includes retry mechanisms for finding iframes and result elements. If issues persist, verify the XPaths used in the script are still valid by inspecting the target website.

### Logging

-   Check `logs.log` for detailed error messages and events to help diagnose issues.

## Contributing

Contributions are welcome! Please follow these steps:

### Fork the Repository

### Create a Feature Branch

```bash
git checkout -b feature/YourFeature
```

### Commit Your Changes

```bash
git commit -m "Add your message"
```

### Push to the Branch

```bash
git push origin feature/YourFeature
```

### Open a Pull Request

## License

This project is licensed under the MIT License.

---

**Disclaimer**: This app does not guarantee financial gain and is for informational purposes only. Ensure you understand the limitations and use it responsibly. This script is provided "as is" without any warranties. Use it at your own risk.
