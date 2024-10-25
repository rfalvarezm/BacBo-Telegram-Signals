from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Initialize WebDriver
driver = webdriver.Chrome()

# Open the target webpage
driver.get('https://www.bettilt504.com/pt/game/bac-bo/real')
mainWindow = driver.window_handles[0]

# Strategy settings
strategyLimits = ['PPT=B', 'BBP=P']
maxGales = 2

# State variables
isEntryAllowed = True
isGreen = False
isGaleActive = False
isRed = False
currentStrategy = []
currentBet = []
galeCount = 0

# Variables to store results
resultsList = []
prevResults = []

def executeStrategy(resultsList):
    """
    Executes the betting strategy based on current results and state variables.
    """
    global isEntryAllowed, isGreen, isGaleActive, isRed, currentStrategy, currentBet, galeCount

    if isEntryAllowed:
        for limit in strategyLimits:
            currentStrategy = list(limit.split('=')[0])
            currentBet = limit.split('=')[1]

            if resultsList[:len(currentStrategy)] == currentStrategy:
                print(f'Entry on {currentBet}')
                isEntryAllowed = False
                isGreen = True
                isGaleActive = True
                break
        return

    elif resultsList[0] == currentBet and isGreen:
        print('GREEN')
        resetState()
        return

    elif resultsList[0] == 'T' and isGreen:
        print('GREEN - TIE')
        resetState()
        return

    elif resultsList[0] == 'T' and resultsList[0] == currentBet and isGaleActive:
        galeCount += 1
        print(f'GALE {galeCount}')
        if galeCount >= maxGales:
            isGaleActive = False
            isRed = True
        return

    elif resultsList[0] == 'T' and resultsList[0] == currentBet and isRed:
        print('RED')
        resetState()
        return

def resetState():
    """
    Resets the state variables after each bet resolution.
    """
    global isEntryAllowed, isGreen, isGaleActive, isRed, galeCount
    isEntryAllowed = True
    isGreen = False
    isGaleActive = False
    isRed = False
    galeCount = 0

def fetchResults():
    """
    Navigates through nested iframes to extract the latest game results.
    """
    # Switch to the main window
    driver.switch_to.window(mainWindow)

    # Wait and switch to the first iframe
    while not driver.find_elements(By.XPATH, '/html/body/div[2]/div[1]/div[3]/div/div/div/div[2]/div[2]/div/iframe'):
        time.sleep(2)
    iframe1 = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[3]/div/div/div/div[2]/div[2]/div/iframe')
    driver.switch_to.frame(iframe1)

    # Wait and switch to the second iframe
    while not driver.find_elements(By.XPATH, '/html/body/iframe'):
        time.sleep(2)
    iframe2 = driver.find_element(By.XPATH, '/html/body/iframe')
    driver.switch_to.frame(iframe2)

    # Wait and switch to the third iframe
    while not driver.find_elements(By.XPATH, '/html/body/div[5]/div[2]/iframe'):
        time.sleep(2)
    iframe3 = driver.find_element(By.XPATH, '/html/body/div[5]/div[2]/iframe')
    driver.switch_to.frame(iframe3)

    # Wait for the target element and extract results
    while not driver.find_elements(By.XPATH, '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div'):
        time.sleep(2)
    resultElement = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div')
    return resultElement.text.split()[::-1][:10]

# Main loop to continuously check and display new results
while True:
    resultsList = fetchResults()
    if resultsList != prevResults:
        prevResults = resultsList
        print(resultsList)
        executeStrategy(resultsList)
