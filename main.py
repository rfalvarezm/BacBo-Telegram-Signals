import os
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from concurrent.futures import ThreadPoolExecutor
import traceback

# =========================
# Configuration and Setup
# =========================

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
WIN_STICKER_ID = os.getenv('WIN_STICKER_ID')  # Sticker file ID from .env
LOSS_STICKER_ID = os.getenv('LOSS_STICKER_ID')  # Loss sticker file ID from .env

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
    raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set in the .env file.")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

logging.basicConfig(
    filename='logs.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# =========================
# Bet Messages and Colors
# =========================

# Define colors and messages for each bet type
BET_COLORS = {
    'P': '🔵',  # Blue
    'B': '🔴',  # Red
    'T': '🟡'   # Yellow (for tie protection)
}

BET_MESSAGES = {
    'P': "🚨 ENTRY CONFIRMED\n🎲 BET ON COLOR ({color})\n🎯 PROTECT IN TIE ({tie_color})",
    'B': "🚨 ENTRY CONFIRMED\n🎲 BET ON COLOR ({color})\n🎯 PROTECT IN TIE ({tie_color})"
}

GALE_MESSAGE = "📉 GALE ATTEMPT {attempt}"

TIE_COLOR = BET_COLORS['T']

def get_bet_message(bet_type):
    """
    Generates a message for the specified bet type (P, B, or T).
    
    :param bet_type: The type of bet ('P' or 'B')
    :return: Customized message string
    """
    color = BET_COLORS.get(bet_type, '❓')  # Default to '❓' if type is not recognized
    message_template = BET_MESSAGES.get(bet_type, "Bet type not recognized.")
    return message_template.format(color=color, tie_color=TIE_COLOR)

def get_gale_message(gale_count, bet_type):
    """
    Generates a message for a Gale attempt.
    
    :param gale_count: The current Gale attempt number
    :param bet_type: The type of bet ('P' or 'B')
    :return: Customized Gale message string
    """
    color = BET_COLORS.get(bet_type, '❓')
    return GALE_MESSAGE.format(attempt=gale_count, color=color)

# =========================
# Scoreboard Tracking
# =========================

class Scoreboard:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.consecutive_wins = 0
        self.total_attempts = 0

    def record_win(self):
        self.wins += 1
        self.consecutive_wins += 1
        self.total_attempts += 1

    def record_loss(self):
        self.losses += 1
        self.total_attempts += 1
        self.consecutive_wins = 0

    def calculate_assertivity_rate(self):
        if self.total_attempts == 0:
            return 0.0
        return round((self.wins / self.total_attempts) * 100, 2)

    def generate_scoreboard_message(self):
        return (
            f"📃 SCOREBOARD\n"
            f"🟢 Wins: {self.wins} 🔴 Losses: {self.losses}\n"
            f"📊 Consecutive Wins: {self.consecutive_wins}\n"
            f"🎯 Assertivity Rate: {self.calculate_assertivity_rate()}%"
        )

scoreboard = Scoreboard()

# =========================
# Telegram Messaging
# =========================

async def send_telegram_message(message=None, is_win=False, is_loss=False):
    """
    Sends a message to the specified Telegram channel asynchronously. Sends a sticker if it's a win or loss.
    
    :param message: The message to send (optional).
    :param is_win: Boolean indicating if the message is a win event.
    :param is_loss: Boolean indicating if the message is a loss event.
    """
    try:
        # Send win sticker if it's a win and WIN_STICKER_ID is set
        if is_win and WIN_STICKER_ID:
            await bot.send_sticker(chat_id=TELEGRAM_CHANNEL_ID, sticker=WIN_STICKER_ID)
            logging.info("🏆 Win sticker sent.")
        # Send loss sticker if it's a loss and LOSS_STICKER_ID is set
        elif is_loss and LOSS_STICKER_ID:
            await bot.send_sticker(chat_id=TELEGRAM_CHANNEL_ID, sticker=LOSS_STICKER_ID)
            logging.info("🔴 Loss sticker sent.")
        # Send the message only if it's not a win/loss or no sticker ID is available
        elif message:
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
            logging.info(f"✅ Message sent: {message}")
    except TelegramError as e:
        # Log the error but do not send it to Telegram
        logging.error(f"❌ Failed to send message: {e}")

# =========================
# Betting Strategy Class
# =========================

class BettingStrategy:
    def __init__(self, strategies, max_gales=2):
        """
        Initializes the betting strategy.

        :param strategies: List of dictionaries with patterns and corresponding bets.
        :param max_gales: Maximum number of gales allowed.
        """
        self.strategies = strategies
        self.max_gales = max_gales
        self.is_entry_allowed = True
        self.is_green = False
        self.is_gale_active = False
        self.is_red = False
        self.current_strategy = None
        self.current_bet = None
        self.gale_count = 0

    async def execute_strategy(self, results_list):
        """
        Executes the betting strategy based on current results.

        :param results_list: List of the latest results.
        """
        if self.is_entry_allowed:
            for strategy in self.strategies:
                pattern = strategy['pattern']
                bet = strategy['bet']
                if results_list[:len(pattern)] == pattern:
                    
                    message = get_bet_message(bet)  # Use the custom message
                    print(message)
                    await send_telegram_message(message)
                    self.is_entry_allowed = False
                    self.is_green = True
                    self.is_gale_active = True
                    self.current_strategy = strategy
                    self.current_bet = bet
                    break
            return

        if not self.current_strategy:
            return

        if results_list[0] == self.current_bet and self.is_green:
            scoreboard.record_win()
            print("✅ WIN!")
            await send_telegram_message(is_win=True)  # Send only the win sticker
            await send_telegram_message(scoreboard.generate_scoreboard_message())
            await self.reset_state()
            return

        if results_list[0] == 'T' and self.is_green:
            scoreboard.record_win()
            print("✅ WIN!(tie)")
            await send_telegram_message(is_win=True)
            await send_telegram_message(scoreboard.generate_scoreboard_message())
            await self.reset_state()
            return

        if results_list[0] != self.current_bet and self.is_green and self.is_gale_active:
            self.gale_count += 1
            message = get_gale_message(self.gale_count, self.current_bet)  # Custom Gale message
            await send_telegram_message(message)
            if self.gale_count >= self.max_gales:
                self.is_gale_active = False
                self.is_red = True
            return

        if self.is_red:
            scoreboard.record_loss()
            print("🔴 LOSS!")
            await send_telegram_message(is_loss=True)
            await send_telegram_message(scoreboard.generate_scoreboard_message())
            await self.reset_state()
            return

    async def reset_state(self):
        """
        Resets the state variables after each bet resolution.
        """
        self.is_entry_allowed = True
        self.is_green = False
        self.is_gale_active = False
        self.is_red = False
        self.current_strategy = None
        self.current_bet = None
        self.gale_count = 0
        logging.info("🔄 State has been reset.")

# =========================
# Selenium Fetch Results
# =========================

def sync_fetch_results(driver, main_window):
    """
    Synchronous function to fetch results using Selenium.

    :param driver: WebDriver instance.
    :param main_window: Handle of the main window.
    :return: Dict with either 'results' or 'error' key.
    """
    try:
        # Switch back to the main window
        driver.switch_to.window(main_window)

        # Define iframe XPaths
        iframe_paths = [
            '/html/body/div[2]/div[1]/div[3]/div/div/div/div[2]/div[2]/div/iframe',
            '/html/body/iframe',
            '/html/body/div[5]/div[2]/iframe'
        ]

        # Navigate through the iframes
        for path in iframe_paths:
            try:
                # Wait until the iframe is present and switch to it
                iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, path)))
                driver.switch_to.frame(iframe)
            except TimeoutException:
                message = f"Iframe not found: {path}"
                logging.warning(message)
                continue

        # Wait for the result element to be present
        target_xpath = '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div'
        result_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, target_xpath)))

        # Extract and process the results
        results_text = result_element.text
        results = results_text.split()[::-1][:3][::-1]
        message = f"🔍 Fetched Results: {results}"
        print(message)
        logging.info(message)
        return {"results": results}

    except NoSuchElementException as e:
        message = f"❌ Element not found: {e}\n{traceback.format_exc()}"
        logging.error(message)
        return {"error": message}
    except TimeoutException as e:
        message = f"❌ Timeout while waiting for an element: {e}\n{traceback.format_exc()}"
        logging.error(message)
        return {"error": message}
    except Exception as e:
        message = f"❌ General error occurred: {e}\n{traceback.format_exc()}"
        logging.error(message)
        return {"error": message}
    finally:
        # Always switch back to the main window to avoid issues with further interactions
        driver.switch_to.default_content()

async def async_fetch_results(executor, driver, main_window):
    """
    Asynchronously fetches results using Selenium by running the synchronous fetch in a thread.

    :param executor: ThreadPoolExecutor instance.
    :param driver: WebDriver instance.
    :param main_window: Handle of the main window.
    :return: Dict with either 'results' or 'error' key.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, sync_fetch_results, driver, main_window)

# =========================
# Main Function
# =========================

async def main():
    # Initialize WebDriver
    driver = webdriver.Chrome()

    try:
        # Open the target webpage
        driver.get('https://www.bettilt504.com/pt/game/bac-bo/real')
        main_window = driver.window_handles[0]

        # Define the strategies
        strategies = [
            {'pattern': ['P', 'P', 'P'], 'bet': 'B'},  # 3 P = bet B and make 2 gales
            {'pattern': ['B', 'B', 'B'], 'bet': 'P'},  # 3 B = bet P and make up to 2 gales
            {'pattern': ['B', 'B', 'P'], 'bet': 'P'},  # 2 B and 1 P = bet P and make up to 2 gales
            {'pattern': ['P', 'P', 'B'], 'bet': 'B'},  # 2 P and 1 B = bet B and make up to 2 gales
        ]

        # Initialize the betting strategy
        betting_strategy = BettingStrategy(strategies=strategies, max_gales=2)

        # Variable to store previous results
        prev_results = []

        # Set up a ThreadPoolExecutor for blocking operations
        executor = ThreadPoolExecutor(max_workers=1)

        # Main loop to monitor and execute bets
        while True:
            # Asynchronously fetch results using Selenium
            result = await async_fetch_results(executor, driver, main_window)

            if "error" in result:
                # Do not send error messages to Telegram
                logging.error(f"⚠️ {result['error']} Retrying...")
                await asyncio.sleep(5)
                continue

            results_list = result.get("results", [])

            if not results_list:
                logging.warning("⚠️ No results obtained. Retrying...")
                await asyncio.sleep(5)
                continue

            # Check if the newly fetched results are different from the previous ones
            if results_list != prev_results:
                prev_results = results_list
                await betting_strategy.execute_strategy(results_list)
            else:
                logging.info("🔄 No new results. Waiting for updates...")

            # Wait for a while before checking again
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        message = "⏹ Program interrupted by user."
        logging.info(message)
    except Exception as e:
        message = f"❌ An unexpected error occurred: {e}"
        logging.error(message)
    finally:
        driver.quit()
        message = "🔒 WebDriver has been closed."
        logging.info(message)

# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    asyncio.run(main())
