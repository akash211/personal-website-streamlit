from ConsoleToDatabase import *

a = ActionChains(bot)

t = bot.find_elements(By.CLASS_NAME, 'textleft')[3]

# Getting breakup and dividend details
a.move_to_element(t).perform()
bot.find_elements(By.CLASS_NAME, 'context-menu-button')[3].click()

bot.find_element(By.XPATH, '//*[contains(text(), "breakdown")]').click()
delay()
breakdown = pd.read_html(bot.page_source)[1]
bot.find_element(By.CLASS_NAME, 'close-modal').click()
delay()
a.move_to_element(t).perform()
bot.find_elements(By.CLASS_NAME, 'context-menu-button')[3].click()
WebDriverWait(bot, wait_).until(
    EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "dividend")]'))
)
bot.find_element(By.XPATH, '//*[contains(text(), "dividend")]').click()
delay()
dividend_ = pd.read_html(bot.page_source)[1]





