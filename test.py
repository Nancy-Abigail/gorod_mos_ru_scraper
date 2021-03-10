from selenium.webdriver import Chrome
from main import count_pages, read_page, create_object


def test_page_count():
    driver = Chrome('selenium/chromedriver.exe')

    driver.get('https://gorod.mos.ru/index.php?show=problem&'
               f'tab={"solvedProblems"}&zone=101&district={102}&m={6}&y={2012}')
    print(count_pages(driver))

    driver.get('https://gorod.mos.ru/index.php?show=problem&'
               f'tab={"solvedProblems"}&zone=101&district={102}&m={6}&y={2016}')
    print(count_pages(driver))

    driver.close()


def test_read_page():
    driver = Chrome('selenium/chromedriver.exe')

    driver.get('https://gorod.mos.ru/index.php?show=problem')
    read_page(driver)

    driver.close()


def test_create_object():
    link = 'https://gorod.mos.ru/?show=objects&id=355816'
    create_object(link)


test_read_page()
