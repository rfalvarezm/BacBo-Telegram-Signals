from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

# Open the webpage
driver.get('https://www.bettilt504.com/pt/game/bac-bo/real')

# Wait for the first iframe to load and switch to it
while len(driver.find_elements(By.XPATH, '/html/body/div[2]/div[1]/div[3]/div/div/div/div[2]/div[2]/div/iframe')) == 0:
    time.sleep(2)

iframe_1 = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[3]/div/div/div/div[2]/div[2]/div/iframe')
driver.switch_to.frame(iframe_1)

# Wait for the second iframe inside the first iframe
while len(driver.find_elements(By.XPATH, '/html/body/iframe')) == 0:
    time.sleep(2)

iframe_2 = driver.find_element(By.XPATH, '/html/body/iframe')
driver.switch_to.frame(iframe_2)

# Wait for the third iframe to load within the second iframe
while len(driver.find_elements(By.XPATH, '/html/body/div[5]/div[2]/iframe')) == 0:
    time.sleep(2)

iframe_3 = driver.find_element(By.XPATH, '/html/body/div[5]/div[2]/iframe')
driver.switch_to.frame(iframe_3)

# Wait for the target element to load within the third iframe
while len(driver.find_elements(By.XPATH, '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div')) == 0:
    time.sleep(2)

# Extract text from the target element
result_element = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div')
results = result_element.text.split()

print(results[::-1])

time.sleep(1000)
