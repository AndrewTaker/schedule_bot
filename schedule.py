import datetime
import os
from babel.dates import format_datetime
from urllib.parse import quote
from urllib.request import urlretrieve
from dataclasses import dataclass

import openpyxl
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from date_ranges import LETTERS_PER_MONTH

load_dotenv()
SCHEDULE_URL: str = os.getenv('SCHEDULE_URL')
HE_URL: str = os.getenv('HE_URL')
GROUP_NAME: str = os.getenv('GROUP_NAME')
WEBSITE_DATE_FORMAT: str = '%d.%m.%y %H:%M'
UPDATE_DATE_FILENAME: str = 'last_update_date.txt'
CURRENT_MONTH: str = format_datetime(format='LLLL', locale='ru_RU')


@dataclass
class Schedule:
    """
    Simple class to hold schedule data structured.
        name: file name as per webpage
        weight: file weight as per webpage
        date: date of file posted
        url: direct download url
    """
    name: str
    weight: str
    date: datetime.datetime
    url: str


def process_excel_file(filename, group_name=GROUP_NAME) -> list[dict]:
    """
    Processes downloaded excel file.
    Returns list of parsed schedule dictionaries.
    """
    schedule_list = []
    workbook = openpyxl.load_workbook(filename, read_only=True)
    worksheet = workbook[group_name]
    rows = create_ranges()
    for row in rows:
        for range in row:
            data = make_matrix(range, worksheet)
            schedule = parse_schedule(data)
            schedule_list.append(schedule)
    workbook.close()
    return schedule_list


def create_single_range(letters: list) -> list[str]:
    """
    Creates a string of range for a single week.
    Range format is "A1:A20".
    """
    template = '{}{}:{}{}'
    ranges = []
    first_row = 10
    second_row = 24
    addition = 15
    schedule_column_size = 6
    for _ in range(schedule_column_size):
        _range = template.format(letters[0], first_row, letters[1], second_row)
        ranges.append(_range)
        first_row += addition
        second_row += addition
    return ranges


def create_ranges() -> list[list[str]]:
    """
    Creates a list of lists with ranges.
    Every list equals to a single week.
    """
    return [
        create_single_range(row) for row in LETTERS_PER_MONTH[CURRENT_MONTH]
    ]


def make_matrix(range: str, worksheet: openpyxl.Workbook) -> list[list[str]]:
    """
    Creates a matrix of worksheet rows.
    """
    matrix = []
    for row in worksheet[range]:
        matrix.append([cell.value for cell in row])
    return matrix


def download_file(url: str, date: datetime.datetime) -> tuple:
    """
    Downloads schedule as an .xlsx.
    Returns a tuple with a filepath and HTTPMessage.
    """
    filename = f"{datetime.datetime.strftime(date, '%d_%m_%y')}.xlsx"
    return urlretrieve(url, filename)


def get_data() -> Schedule:
    """
    Parses all the data from schedule page.
    Returns a Schedule class instance.
    """
    response = requests.get(SCHEDULE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table').tbody.find_all('tr')
    lookup = f'икиип бакалавриат {CURRENT_MONTH.lower()}'

    for i in table:
        context = i.td.a
        if (
            context and
            lookup in context.get_text(strip=True).lower()
        ):
            name, weight, date = map(
                lambda x: x.get_text(strip=True),
                i.find_all('td')
            )
            url = HE_URL + quote(i.td.a.get('href'))
            date = datetime.datetime.strptime(date, WEBSITE_DATE_FORMAT)
            save_last_date_update(date)
            clear_xlsx_files()
            download_file(url, date)
    return Schedule(name, weight, date, url)


def save_last_date_update(date: str) -> None:
    """
    Saves last schedule update date to .txt file.
    """
    with open(UPDATE_DATE_FILENAME, 'w') as file:
        file.write(datetime.datetime.strftime(date, WEBSITE_DATE_FORMAT))


def get_last_date_update() -> str:
    """
    Gets last schedule update date from .txt file.
    Returns the date as a string.
    """
    with open(UPDATE_DATE_FILENAME, 'r') as file:
        return file.readline()


def parse_schedule(matrix) -> dict:
    """
    Parses a matrix of .xlsx rows.
    Return a dictionary:
        {
            'date': str,
            'day': str,
            '<lesson time: str>: <lesson info: str>,
            '<lesson time: str>: <lesson info: str>,
            '<lesson time: str>: <lesson info: str>,
            '<lesson time: str>: <lesson info: str>,
            '<lesson time: str>: <lesson info: str>,
        }
    """
    schedule = {
        'date': datetime.datetime.strftime(matrix[0][1], '%d.%m.%y'),
        'day': matrix[0][0]
    }
    for i, row in enumerate(matrix):
        if row.count(None) > 1 or i == 0:
            continue
        if row[1] is None:
            schedule[row[0]] = '---'
        elif row[0] is not None:
            schedule[row[0]] = row[1]
        else:
            _time = matrix[i-1][0]
            schedule[_time] += f'<u>{row[1]}</u>'
    return schedule


def schedule_prettify(schedule: dict) -> str:
    """
    Makes a string from schedule dictionary.
    Representable for telegram message.
    """
    string = (
        f'📆<strong>{schedule["date"]}, '
        f'{schedule["day"]}</strong>📆' + '\n\n'
    )
    # Forced to specify last index.
    # Formatting doesn't work for the last day of the week without it.
    for k, v in list(schedule.items())[2:-1]:
        string += f'⌛️<strong>{k}</strong>' + '\n'
        string += f'<i>{v}</i>' + '\n\n'
    return string


def is_schedule_updated(
        schedule: Schedule,
        last_update_date: datetime.datetime = datetime.datetime.now(),
) -> bool:
    """
    Checks if upload date equals last stored date.
    Returns True if differs, False otherwise.
    """
    return schedule.date != last_update_date


def get_file() -> list[dict]:
    """
    Opens local .xlsx file for processing.
    Returns a list of parsed schedule dictionaries.
    """
    current_directory = os.getcwd()
    for file in os.listdir(current_directory):
        if file.endswith('.xlsx'):
            return process_excel_file(file)


def clear_xlsx_files() -> None:
    """Clears all the .xlsx files in directory."""
    current_directory = os.getcwd()
    for file in os.listdir(current_directory):
        if file.endswith('.xlsx'):
            os.remove(file)
