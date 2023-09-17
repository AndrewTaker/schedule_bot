import datetime
import os
import time
from urllib.parse import quote
from urllib.request import urlretrieve
from dataclasses import dataclass

import openpyxl
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
SCHEDULE_URL: str = os.getenv('SCHEDULE_URL')
HE_URL: str = os.getenv('HE_URL')
GROUP_NAME: str = os.getenv('GROUP_NAME')


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

    def date_as_string(self):
        return datetime.datetime.strftime(self.date, '%y%m%d')


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
    letters = [
        ['B', 'C'],
        ['D', 'E'],
        ['F', 'G'],
        ['H', 'I'],
        ['J', 'K'],
    ]
    return [create_single_range(row) for row in letters]


def make_matrix(range: str, worksheet: openpyxl.Workbook) -> list[list[str]]:
    """
    Creates a matrix of worksheet rows.
    """
    matrix = []
    for row in worksheet[range]:
        matrix.append([cell.value for cell in row])
    return matrix


def download_file(url, date) -> tuple:
    """
    Downloads schedule as an .xlsx.
    Returns a tuple with a filepath and HTTPMessage.
    """
    filename = f"{datetime.datetime.strftime(date, '%y%m%d')}.xlsx"
    return urlretrieve(url, filename)


def get_data() -> tuple:
    """
    Parses all the data from schedule page.
    Returns a Schedule class instance.
    """
    response = requests.get(SCHEDULE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table').tbody.find_all('tr')

    for i in table:
        if (
            i.td.a and
            'икиип бакалавриат' in i.td.a.get_text(strip=True).lower()
        ):
            name, weight, date = map(
                lambda x: x.get_text(strip=True),
                i.find_all('td')
            )
            url = HE_URL + quote(i.td.a.get('href'))
            date = datetime.datetime.strptime(date, '%d.%m.%y %H:%M')
    return Schedule(name, weight, date, url)


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
    # Formatting doesn't work the last day of the week without it.
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
    Returns a list of parsed schedule dictionaries
    or raises FileNotFoundError.
    """
    current_directory = os.getcwd()
    print(current_directory)
    for file in os.listdir(current_directory):
        if file.endswith('.xlsx'):
            print(file)
            return process_excel_file(file)


def clear_xlsx_files() -> None:
    """Clears all the .xlsx files in directory."""
    current_directory = os.getcwd()
    for file in os.listdir(current_directory):
        if file.endswith('.xlsx'):
            os.remove(file)


def start_monitoring():
    last_update_date = datetime.datetime.now().replace(microsecond=0)
    while True:
        print(f'last update at: {last_update_date}')
        schedule: Schedule = get_data()
        print(f'current schedule upload date: {schedule.date}')
        if is_schedule_updated(schedule, last_update_date):
            clear_xlsx_files()
            print('dates differ, downloading file')
            last_update_date = schedule.date
            file = download_file(schedule.url, schedule.date)
            print(f'downloaded {file[0]}')
        else:
            print('nothing changed')
        print('sleeping\n\n')
        time.sleep(10)


if __name__ == '__main__':
    clear_xlsx_files()