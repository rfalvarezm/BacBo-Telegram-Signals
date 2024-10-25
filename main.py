import os
import asyncio
import logging
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from concurrent.futures import ThreadPoolExecutor

# =========================
# Configuration and Setup
# =========================

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

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
# Telegram Messaging
# =========================

async def send_telegram_message(message):
    """
    Sends a message to the specified Telegram channel asynchronously.

    :param message: The message to send.
    """
    try:
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
        logging.info(f"✅ Message sent: {message}")
        print(f"✅ Message sent: {message}")
    except TelegramError as e:
        # Log the error but do not send it to Telegram
        logging.error(f"❌ Failed to send message: {e}")
        print(f"❌ Failed to send message: {e}")

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
                    message = f'📈 Entry on {bet}'
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
            message = '✅ GREEN - Win!'
            print(message)
            await send_telegram_message(message)
            await self.reset_state()
            return

        if results_list[0] == 'T' and self.is_green:
            message = '🔄 GREEN - TIE!'
            print(message)
            await send_telegram_message(message)
            await self.reset_state()
            return

        if results_list[0] != self.current_bet and self.is_green and self.is_gale_active:
            self.gale_count += 1
            message = f'📉 GALE {self.gale_count}'
            print(message)
            await send_telegram_message(message)
            if self.gale_count >= self.max_gales:
                self.is_gale_active = False
                self.is_red = True
            return

        if self.is_red:
            message = '🚫 RED - Gale limit reached.'
            print(message)
            await send_telegram_message(message)
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
        print("🔄 State has been reset.")

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
            # Wait until the iframe is present
            for _ in range(10):
                try:
                    iframe = driver.find_element(By.XPATH, path)
                    driver.switch_to.frame(iframe)
                    break
                except NoSuchElementException:
                    time.sleep(1)
            else:
                message = f"Iframe not found: {path}"
                print(message)
                return {"error": message}

        # Wait for the result element to be present
        target_xpath = '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div'
        for _ in range(10):
            try:
                result_element = driver.find_element(By.XPATH, target_xpath)
                break
            except NoSuchElementException:
                time.sleep(1)
        else:
            message = "Result element not found."
            print(message)
            return {"error": message}

        # Extract and process the results
        results_text = result_element.text
        results = results_text.split()[::-1][:10]
        message = f"🔍 Fetched Results: {results}"
        print(message)
        logging.info(message)
        return {"results": results}

    except Exception as e:
        message = f"❌ Error fetching results: {e}"
        print(message)
        logging.error(message)
        return {"error": message}

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
                print("Error obtained while fetching results. Retrying...")
                # Do not send error messages to Telegram
                logging.error(f"⚠️ {result['error']} Retrying...")
                await asyncio.sleep(5)
                continue

            results_list = result.get("results", [])

            if not results_list:
                print("No results obtained. Retrying...")
                logging.warning("⚠️ No results obtained. Retrying...")
                await asyncio.sleep(5)
                continue

            # Check if the newly fetched results are different from the previous ones
            if results_list != prev_results:
                prev_results = results_list
                await betting_strategy.execute_strategy(results_list)
            else:
                print("🔄 No new results. Waiting for updates...")
                logging.info("🔄 No new results. Waiting for updates...")

            # Wait for a while before checking again
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        message = "⏹ Program interrupted by user."
        print(message)
        logging.info(message)
    except Exception as e:
        message = f"❌ An unexpected error occurred: {e}"
        print(message)
        logging.error(message)
    finally:
        driver.quit()
        message = "🔒 WebDriver has been closed."
        print(message)
        await send_telegram_message(message)

# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    asyncio.run(main())
