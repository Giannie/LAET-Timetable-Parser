from datetime import datetime, date, timedelta
from pytz import timezone
import os

import pandas as pd
import icalendar as ical

class CustomFileNotFoundError(Exception):
    def __init__(self):
        self.message = "File not found"

    def __str__(self):
        return self.message


class CalendarNotFoundError(CustomFileNotFoundError):
    def __init__(self):
        self.message = "Could not find calendar file"


class TimetableNotFoundError(CustomFileNotFoundError):
    def __init__(self):
        self.message = "Could not find timetable file"


class DirectoryNotFoundError(Exception):
    def __init__(self):
        self.message = "Could not find directory"


def get_weeks(filename):
    """
    Returns a list of dates for weeks 1 and 2. Given dates
    are the sunday at the beginning of the week
    """
    weeks = {
        1: [],
        2: []
    }
    try:
        data = pd.read_csv(filename, dtype={"week no ": "Int64", "week no": "Int64"})
    except FileNotFoundError:
        raise CalendarNotFoundError
    data = data[data["week no "].notnull()]
    for index in data.index:
        row = data.loc[index]
        week_no = row["week no "]
        date = datetime.strptime(row["start"], "%d/%m/%Y").date()
        weeks[week_no].append(date)
    return weeks


def read_data(filename):
    """
    Load all timetable data from a csv file.
    Return a pandas DataFrame
    """
    try:
        data = pd.read_csv(filename)
    except FileNotFoundError:
        raise TimetableNotFoundError

    data = data[data["StartEndTime"].notnull()]
    data = data[data["ClassName"].notnull()]
    data = data[data["ClassName"] != "Blanking"]
    data = data[~data["PeriodName"].isin(["AM", "PM"])]
    return data


def get_teacher_names(data):
    """
    Get the names of each teacher in the DataFrame.
    """
    return data.Name.unique()


def get_teacher_data(df, name):
    """
    Return a DataFrame containing only the data referring
    to the given teacher.
    """
    return df[df["Name"] == name]


def get_summary_dict(data):
    """
    Return a dictionary whose keys are the names of teachers
    and values are a DataFrame with all of that teacher's
    data.
    """
    d = {}
    for teacher in get_teacher_names(data):
        teacher_data = get_teacher_data(teacher, data)
        teacher_data = teacher_data[teacher_data["ClassName"].notnull()]
        d[teacher] = teacher_data
    return d


def get_date_times(row, weeks):
    """
    Return a list of datetimes related to a row.
    """
    date_times = []
    week_no = row["TimetableWeek"]
    week_starts = weeks[week_no]
    day_no = row["WeekDayNo"]
    if week_no == 2:
        day_no -= 5
    start_time, end_time = row["StartEndTime"].split(" - ")
    start_time = datetime.strptime(start_time, "%H:%M").time()
    end_time = datetime.strptime(end_time, "%H:%M").time()
    for week_start in week_starts:
        start = datetime.combine(week_start, start_time)
        start += timedelta(days=int(day_no))
        end = datetime.combine(week_start, end_time)
        end += timedelta(days=int(day_no))
        date_times.append((start, end))
    return date_times


def create_events(row, weeks):
    """
    Create event from a row, looking up the relevant weeks.
    """
    events = []
    event = ical.Event()
    event.add('summary', row["ClassName"])
    event.add('location', row['Room'])
    event.add('categories', [row["ClassName"], row['Subject'], 'auto-generated'])
    for start, end in get_date_times(row, weeks):
        local_event = event.copy()
        local_event.add("dtstart", start)
        local_event.add("dtend", end)
        events.append(local_event)
    return events


def create_calendar(data, teacher, weeks):
    """
    Creates a calendar from the data given.
    """
    calendar = ical.Calendar()
    calendar.add('summary', teacher)
    teacher_data = get_teacher_data(data, teacher)
    for index in teacher_data.index:
        row = teacher_data.loc[index]
        for event in create_events(row, weeks):
            calendar.add_component(event)
    return calendar


class TimetableParser:
    def __init__(self, timetable_file, calendar_file):
        self.weeks = get_weeks(calendar_file)
        self.timetable_data = read_data(timetable_file)
        self.calendars = {}
    
    def create_calendars(self):
        """
        Creates iCal files for each teacher in data.
        """
        for teacher in self.timetable_data.Name.unique():
            self.calendars[teacher] = create_calendar(self.timetable_data, teacher, self.weeks)
    
    def save_calendars(self, directory):
        """
        Saves generated calendars to files in directory
        """
        if not(os.path.isdir(directory)):
            raise DirectoryNotFoundError
        for teacher, calendar in self.calendars.items():
            with open(os.path.join(directory, teacher + ".ics"), "wb") as f:
                f.write(calendar.to_ical())
