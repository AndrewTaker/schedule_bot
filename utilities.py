import datetime


def get_tomorrow() -> str:
    """
    Get tomorrow's date as a string.
    """
    datetime_today: datetime.datetime = datetime.datetime.now().date()
    tomorrow: datetime.datetime = datetime_today + datetime.timedelta(1)
    return tomorrow.strftime('%d.%m.%y')


def get_week() -> int:
    """
    Get current week as per ISO.
    """
    datetime_today: datetime.datetime = datetime.datetime.now().date()
    iso_week = datetime_today.isocalendar().week
    return iso_week


def as_datetime(string_date) -> datetime.datetime:
    """
    Returns string date as a datetime object.
    """
    return datetime.datetime.strptime(string_date, '%d.%m.%y')
