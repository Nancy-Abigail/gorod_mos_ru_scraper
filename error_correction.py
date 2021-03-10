from main import read_all_pages, read_page, read_all_dates, create_object
import json
from selenium.webdriver import Chrome

with open('error_log.txt', 'r') as file:
    error_log = file.readlines()

for line in error_log:
    try:
        data = json.loads(line)
        type = data['type']
        data.pop('type')

        if type == 'create_object':
            create_object(**data)

        elif type == 'read_page':
            tab = data['tab']
            zone = data['zone']
            district = data['district']
            month = data['month']
            year = data['year']
            page = data['page']

            driver = Chrome('selenium/chromedriver.exe')
            driver.get('https://gorod.mos.ru/index.php?show=problem'
                       f'&tab={tab}&zone={zone}&district={district}'
                       f'&m={month}&y={year}&page={page}')
            data['driver'] = driver
            read_page(**data)
            driver.close()

        elif type == 'read_all_pages':
            driver = Chrome('selenium/chromedriver.exe')
            data['driver'] = driver
            read_all_pages(**data)
            driver.close()

        elif type == 'read_all_dates':
            read_all_dates(**data)

        else:
            raise Exception

        with open('error_correction_log.txt', 'r+') as file:
            file.write(f'Success: {line}')

    except Exception as e:
        print(e)
        with open('error_correction_log.txt', 'r+') as file:
            file.write(f'Error: {line}')
