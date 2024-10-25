from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

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

    def execute_strategy(self, results_list):
        """
        Executes the betting strategy based on current results.
        
        :param results_list: List of the latest results.
        """
        if self.is_entry_allowed:
            for strategy in self.strategies:
                pattern = strategy['pattern']
                bet = strategy['bet']
                if results_list[:len(pattern)] == pattern:
                    print(f'Entry on {bet}')
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
            print('GREEN - Win!')
            self.reset_state()
            return

        if results_list[0] == 'T' and self.is_green:
            print('GREEN - TIE!')
            self.reset_state()
            return

        if results_list[0] != self.current_bet and self.is_green and self.is_gale_active:
            self.gale_count += 1
            print(f'GALE {self.gale_count}')
            if self.gale_count >= self.max_gales:
                self.is_gale_active = False
                self.is_red = True
            return

        if self.is_red:
            print('RED - Gale limit reached.')
            self.reset_state()
            return

    def reset_state(self):
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

def fetch_results(driver, main_window):
    """
    Navigates through iframes to extract the latest game results.
    
    :param driver: WebDriver instance.
    :param main_window: Handle of the main window.
    :return: List of the last 10 results.
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
                print(f"Iframe not found: {path}")
                return []

        # Wait for the result element to be present
        target_xpath = '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div'
        for _ in range(10):
            try:
                result_element = driver.find_element(By.XPATH, target_xpath)
                break
            except NoSuchElementException:
                time.sleep(1)
        else:
            print("Result element not found.")
            return []

        # Extract and process the results
        results_text = result_element.text
        results = results_text.split()[::-1][:10]
        return results

    except Exception as e:
        print(f"Error fetching results: {e}")
        return []

def main():
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

        # Main loop to monitor and execute bets
        while True:
            results_list = fetch_results(driver, main_window)
            if not results_list:
                print("No results obtained. Retrying...")
                time.sleep(5)
                continue

            if results_list != prev_results:
                prev_results = results_list
                print(f"Current Results: {results_list}")
                betting_strategy.execute_strategy(results_list)

            # Wait for a while before checking again
            time.sleep(5)

    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
