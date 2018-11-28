import requests
import re
import time
from bs4 import BeautifulSoup, SoupStrainer

def format_month(month_string):
    month_digit="00"
    if (month_string == "Januar"):
        month_digit = "01"
    elif (month_string == "Februar"):
        month_digit = "02"
    elif (month_string =="März"):
        month_digit = "03"
    elif (month_string == "April"):
        month_digit = "04"
    elif (month_string == "Mai"):
        month_digit = "05"
    elif (month_string == "Juni"):
        month_digit = "06"
    elif (month_string =="Juli"):
        month_digit = "07"
    elif (month_string =="August"):
        month_digit = "08"
    elif (month_string =="September"):
        month_digit = "09"
    elif (month_string =="Oktober"):
        month_digit = "10"
    elif (month_string =="November"):
        month_digit = "11"
    elif (month_string =="Dezember"):
        month_digit = "12"
    return month_digit

def convert_date(date):
    day = re.search('\d{1,2}', date).group()
    if (len(day) < 2):
        day = "0" + day
    month = re.search('[A-Z][a-z]*', date).group()
    year = re.search('\d{4}', date).group()
    return (year + '-' + format_month(month) + '-' + day + "T00:00:00+0200")

def find_source(tag):
    liste = []
    for a in tag.find_all('a', href=True):
        liste.append(a['href'])
    return liste

def find_location(tag):
    if ":" in tag.find('h2', class_="node__title node-title").string:
        return re.match('[^:]*', tag.find('h2', class_="node__title node-title").string).group()
    else:
        return ""


# the motivation is not mentionned within the article but articles
# can be classified by motivation by choosing from a list
def check_motivation(tag):
    motivation = {}
    motivation['value'] = tag['value']
    motivation['text'] = tag.string
    motivation['articles'] = []

    # request page with articles about incidents with motivation = value
    r = requests.get('https://response-hessen.de/chronik?field_district_tid=All&field_motivation_tid=' + motivation['value'] + '&page=PAGE')
    html_doc = r.text
    soup = BeautifulSoup(html_doc, 'lxml')

    # check if there's more than one page (using regex to isolate the numbers from the pagelinks)
    try:
        last_page = soup.find('ul', class_='pager').find('li', class_='pager-last last').find('a', href=True)
        motivation['num_pages'] = int(re.search('(?<=page=)(\d*)$', last_page['href']).group())
    except AttributeError:
        motivation['num_pages'] = 0

    articles = soup.find_all('article', class_='node-chronicle')
    for article in articles:
        motivation['articles'].append(article)

    if motivation['num_pages'] > 0:
        # iterating over the hidden pages (making a new get-request for each page)
        counter = 1
        while (motivation['num_pages'] + 1) >= counter:
            r_new = requests.get('https://response-hessen.de/chronik?field_district_tid=All&field_motivation_tid=' + motivation['value'] + '&page=' + str(counter))
            html_doc_new = r_new.text
            soup_new = BeautifulSoup(html_doc_new, 'lxml')
            articles = soup_new.find_all('article', class_='node-chronicle')
            for article in articles:
                motivation['articles'].append(article)
            counter += 1

    return motivation



r = requests.get('https://response-hessen.de/chronik')
html_doc = r.text

# get nice html-code of the page
soup = BeautifulSoup(html_doc, 'lxml')
# print(soup.prettify())

# looking for different categories of motivations
motivations = soup.find('select', id='edit-field-motivation-tid').contents[1:]

entries = {}
id = 1

for motivation_type in motivations:
    motive = check_motivation(motivation_type)
    # the exact format of the data still could be optimized
    for article in motive['articles']:
        entries[id] = {}
        entries[id]['title'] = article.find('h2', class_="node__title node-title").string
        entries[id]['description'] = article.find('p').string
        entries[id]['startDate'] = convert_date(str(article.find('span', class_='date-display-single').string))
        entries[id]['iso3166_2'] = "DE-HE"
        entries[id]['locations'] = find_location(article)
        entries[id]['sources'] = find_source(article)
        entries[id]['motives'] = motive['text']
        id += 1
