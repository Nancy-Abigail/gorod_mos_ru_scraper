from selenium.webdriver import Chrome
from selenium.common.exceptions import NoSuchElementException

districts = []
zone_list = []

driver = Chrome('selenium/chromedriver.exe')

driver.get('https://gorod.mos.ru/?show=problem')
zones_block = driver.find_element_by_xpath('//span[contains(@class,"combo-inner fil-b zone pop")]')

for zone in zones_block.find_elements_by_xpath('./div/div/a'):
    if zone.get_attribute('value') != '0':
        zone_list.append(int(zone.get_attribute('value')))

for zone in zone_list:
    # Зайти на страницу автономного округа
    driver.get(f'https://gorod.mos.ru/?show=problem&zone={zone}')
    # Найти список районов
    districts_block = driver.find_element_by_xpath('//span[contains(@class,"combo-inner fil-b district pop")]')

    # Для всех районов добавить значения в список Districts
    for district in districts_block.find_elements_by_xpath('./div/div/a'):
        if district.get_attribute('value') != '0':
            result = {'zone': zone, 'district': int(district.get_attribute('value'))}
            districts.append(result)

print(districts)

driver.close()
