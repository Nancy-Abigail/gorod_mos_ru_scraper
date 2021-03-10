from lov import dates, districts, tabs, months
from orm import Author, Object, Report
from orm import new_session
from selenium.webdriver import Chrome
import threading
import re


def log_error(type: str, **kwargs):
    # Fill error log row
    row = '{'
    row += f'"type":"{type}"'
    for key, value in kwargs.items():
        row += f',"{key}":"{value}"'
    row += '}\n'

    # Add row to log file
    with open('error_log.txt', 'a+') as file:
        file.write(row)


# noinspection PyBroadException
def create_object(link: str):
    driver = Chrome('selenium/chromedriver.exe')
    driver.get(link)

    try:
        # Get script with object info
        script_text = ''
        scripts = driver.find_elements_by_xpath("//script[@type='text/javascript']")
        for script in scripts:
            if script.get_attribute('innerHTML')[0:15] == ';FE.manageEvent':
                script_text = script.get_attribute('innerHTML')

        # Fill object
        object = Object()
        object.id = int(re.findall('"objectId":[0-9]+', script_text)[0][11:])
        object.type = driver.find_element_by_xpath('//div[@class="col_3c"]/div').text
        object.address = re.findall('"address": "[^"]+"', script_text)[0][12:-1]
        object.lat = re.findall('"objectLat": [0-9.]+,', script_text)[0][12:-1]
        object.lon = re.findall('"objectLon": [0-9.]+,', script_text)[0][12:-1]

        # Push object to DB
        session = new_session()
        object.push(session)
        session.commit()
        session.close()
    except Exception:
        log_error(type='create_object', object_link='link')
        pass

    driver.close()


def create_author(element):
    # Create and fill author
    author = Author()
    author.id = int(re.findall('user_id=[0-9]+', element.get_attribute('href'))[0][8:])
    author.full_name = element.text

    result = author.id

    # Push author to DB
    session = new_session()
    author.push(session)
    session.commit()
    session.close()

    return result


# noinspection PyBroadException
def create_report(element, object_id: int):
    # Create author
    author_element = element.find_element_by_xpath('.//div[contains(@class,"m-name")]/a')
    author_id = create_author(author_element)

    # Create and fill report
    report = Report()
    report.id = int(element.get_attribute('reqnum'))
    report.object_id = object_id
    report.author_id = author_id

    # These variables will be filled later
    report.theme = ''
    report.date = ''
    report.text = ''
    report.image_links = ''

    # Get and fill theme
    try:
        report.theme = element.find_element_by_xpath('.//div[@class="themeText bold"]').text
    except Exception:
        pass

    # Get and fill text
    try:
        report.text = element.find_element_by_xpath('.//div[@class="messageText"]/p').text
    except Exception:
        pass

    # Get and fill report date
    try:
        date_row = element.find_element_by_xpath('.//div[@class="m-date"]').text
        day = re.findall(' [0-9]{2} ', date_row)[0][1:-1]
        month_text = re.findall('Января|Февраля|Марта|Апреля|Мая|Июня|Июля|Августа|Сентября|Октября|Ноября|Декабря',
                                date_row)[0]
        month = months[month_text]
        year = re.findall(' [0-9]{4} ', date_row)[0][1:-1]
        time = re.findall(' [0-9]{2}:[0-9]{2},', date_row)[0][1:-1]

        report.date = f'{year}-{month}-{day} {time}'

    except Exception:
        pass

    # Get first image
    try:
        report.image_links += element.find_element_by_xpath('.//div[@class="messageText"]/div[@class="img-mes"]'
                                                            '/div[@class="img-mes-bg yug"]').get_attribute('original')
    except Exception:
        pass

    # Get other images
    try:
        add_images = element.find_elements_by_xpath('.//div[@class="messageText"]/div[@class="g-box"]/div')
        for image in add_images:
            report.image_links += ';' + image.get_attribute('original')
    except Exception:
        pass

    # Push report to DB
    session = new_session()
    report.push(session)
    session.commit()
    session.close()


def read_page(driver, zone, district, tab, year, month, page):

    try:
        # Get all elements
        elements = driver.find_elements_by_xpath('//div[@class="message-content ctrl-enter-ban"]/div')

        # Objects and reports are represented as flat list. We need to save object before reading a report.
        object_id = ''

        # Iterate through all elements
        for element in elements:

            # If element is an object:
            if element.get_attribute('class') == 'headerCategory':
                # Get object link and ID
                object_link = element.find_element_by_xpath('./div/a').get_attribute('href')
                object_id = int(re.findall('objects&id=[0-9]+', object_link)[0][11:])

                # Call create object
                if not Object.already_exist(object_id):
                    create_object(object_link)

            # If element is a report:
            else:
                create_report(element, object_id)
    except Exception as e:
        print(f'Error at zone={zone}, district={district}, year={year}, month={month}, page=1: {e}')
        log_error(type='read_page', zone=zone, district=district, tab=tab, year=year, month=month, page=page)


def count_pages(driver) -> int:
    max_page = 0
    # noinspection PyBroadException
    try:
        paginator = driver.find_element_by_class_name("pagination")
        page_elements = paginator.find_elements_by_xpath('./a')
        for page_element in page_elements:
            page_number = int(page_element.get_attribute('data-page'))
            if page_number > max_page:
                max_page = page_number
    except Exception:
        pass

    return max_page


def read_all_pages(driver, zone, district, tab, year, month):
    try:
        # Get first page
        driver.get('https://gorod.mos.ru/index.php?show=problem'
                   f'&tab={tab}&zone={zone}&district={district}'
                   f'&m={month}&y={year}')

        # Read first page
        read_page(driver, zone, district, tab, year, month, 1)

        # Check if there are other pages and read them
        pages_amount = count_pages(driver)
        for page in range(2, pages_amount + 1):
            driver.get('https://gorod.mos.ru/index.php?show=problem'
                       f'&tab={tab}&zone={zone}&district={district}'
                       f'&m={month}&y={year}&page={page}')
            read_page(driver, zone, district, tab, year, month, page)
    except Exception as e:
        print(f'Error at zone={zone}, district={district}, year={year}, month={month}: {e}')
        log_error(type='read_all_pages', zone=zone, district=district, tab=tab, year=year, month=month)


def read_all_dates(zone, district, tab):
    try:
        for date in dates:
            driver = Chrome('selenium/chromedriver.exe')
            read_all_pages(driver, zone, district, tab, date['year'], date['month'])
            driver.close()
    except Exception as e:
        print(f'Error at zone={zone}, district={district}, all dates: {e}')
        log_error(type='read_all_dates', zone=zone, district=district, tab=tab)


def run_district_group(district_group, tab):
    for district in district_group:
        read_all_dates(district['zone'], district['district'], tab)


def run_all_districts():
    thread_amount = 10  # Number of parallel threads (was done to increase parser's speed)
    district_groups = []
    for i in range(thread_amount):
        district_groups.append([])

    for i in range(len(districts)):
        district_groups[i % thread_amount].append(districts[i])

    for district_group in district_groups:
        for tab in tabs:
            threading.Thread(target=run_district_group, args=(district_group, tab)).start()


def main():
    # Dear Lord, save us all
    run_all_districts()


if __name__ == '__main__':
    main()
