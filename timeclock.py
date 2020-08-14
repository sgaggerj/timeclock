#! /usr/bin/python3

# A simple time-clock program to keep track of hours.

import sys
import os
import csv
from datetime import datetime, time, timedelta
from pathlib import Path
import shutil
from colorama import Fore, Style


# The data file holding punch-ins and outs.  Data is stored newest to oldest.
DATA_FILE = str(Path.home()) + '/timeclock.csv'
DATETIME_STRING_FORMAT = "%B %d, %Y %H:%M:%S"
NOW = datetime.now()
WORK_HOURS = []

_GREEN = Fore.GREEN
_RESET = Style.RESET_ALL


def red_string(string: str) -> str:
    return Fore.RED + string + _RESET


def green_string(string: str) -> str:
    return _GREEN + string + _RESET


def seconds_to_formatted_hours(seconds: int, highlight=None) -> str:
    return (highlight if highlight else '') + '{:.2f}'.format(seconds / 3600) + (_RESET if highlight else '')


def load_work_hours():
    # Create the file if it doesn't already exist.
    if not os.path.exists(DATA_FILE):
        open(DATA_FILE, mode='w').close()

    # Load any existing hourly data into the list.
    with open(DATA_FILE, mode='r') as csv_file:
        print('Loading data...')
        reader = csv.reader(csv_file)
        for row in reader:
            WORK_HOURS.append(row)


def write_hour_data():

    # Todo: Don't backup an empty file.
    shutil.copy(DATA_FILE, DATA_FILE + '.bak')

    # Write the hourly data to the csv file.
    with open(DATA_FILE, mode='w+') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(WORK_HOURS)


def display_punch_success(action, _time):
    print(f'Punched you {green_string(action)}: {_time.strftime(DATETIME_STRING_FORMAT)}')


def do_punch_in(punch_in_date_time=None):
    # Punch in if there is no dangling punch in already existing.
    # We always work with the first element in the list.
    if not WORK_HOURS or len(WORK_HOURS[0]) == 2:
        if not punch_in_date_time:
            WORK_HOURS.insert(0, [NOW.timestamp()])
        else:
            WORK_HOURS.insert(0, [punch_in_date_time.timestamp()])
        write_hour_data()
        display_punch_success('in', punch_in_date_time or NOW)
        display_current_total()
    elif len(WORK_HOURS[0]) == 1:
        raise SystemExit(f'{red_string("Error")}: Please punch out first.')
    else:
        print(f'{red_string("Something went wrong punching you in.")}')


def do_punch_out(punch_out_date_time=None):
    # Punch out only if there is a dangling punch in.
    # We always work with the first element in the list.
    if not WORK_HOURS or len(WORK_HOURS[0]) == 2:
        print(f'{red_string("Error")}: Please punch in first.')
        sys.exit()
    elif len(WORK_HOURS[0]) == 1:
        if punch_out_date_time is None:
            WORK_HOURS[0] = [WORK_HOURS[0][0], NOW.timestamp()]
        else:
            if float(WORK_HOURS[0][0]) < punch_out_date_time.timestamp():
                WORK_HOURS[0] = [WORK_HOURS[0][0], punch_out_date_time.timestamp()]
            else:
                raise SystemExit(f'{red_string("Your punch-out time cannot be before your punch-in time.")}')
        write_hour_data()
        display_punch_success('out', punch_out_date_time or NOW)
        display_current_total()
    else:
        print(f'{red_string("Something went wrong punching you out.")}')


def display_turn_in_total():
    # This past Monday at midnight
    end_of_previous_week = datetime.combine(NOW - timedelta(days=NOW.weekday()), time())
    # The previous Monday at midnight
    start_of_previous_week = end_of_previous_week - timedelta(7)
    total_seconds_worked = 0
    # Calculate the total number of hours to turn in.
    for entry in WORK_HOURS:
        if len(entry) == 2:
            check_in = float(entry[0])
            if start_of_previous_week.timestamp() <= check_in < end_of_previous_week.timestamp():
                total_seconds_worked += (float(entry[1]) - check_in)

    print(f'Total hours to turn in for last week: {green_string(seconds_to_formatted_hours(total_seconds_worked))}')


def display_current_total():
    # This past Monday at midnight
    start_of_current_week = datetime.combine(NOW - timedelta(days=NOW.weekday()), time())

    days = {
        0: {'title': 'Monday', 'value': 0},
        1: {'title': 'Tuesday', 'value': 0},
        2: {'title': 'Wednesday', 'value': 0},
        3: {'title': 'Thursday', 'value': 0},
        4: {'title': 'Friday', 'value': 0},
        5: {'title': 'Saturday', 'value': 0},
        6: {'title': 'Sunday', 'value': 0}
    }

    # Calculate the current week's hours.
    for entry in WORK_HOURS:
        check_in = float(entry[0])
        diff = 0
        # if the check in was part of the current week
        if len(entry) == 2 and check_in >= start_of_current_week.timestamp():
            diff = float(entry[1]) - check_in
        # Assumption here is that no prior week entry will have just a check-in only.
        elif len(entry) == 1:
            diff = NOW.timestamp() - check_in
        days[datetime.fromtimestamp(check_in).weekday()]['value'] += diff

    print(f'\nSummary for the week of {start_of_current_week.strftime("%m/%d/%Y")}:')
    total_seconds_worked = 0
    total_seconds_worked_today = 0
    for day in days.values():
        total_seconds_worked += day['value']
        display = day['title'] + ' ' + seconds_to_formatted_hours(day['value'])
        if NOW.strftime('%A') == day['title']:
            display = green_string(display)
            total_seconds_worked_today += day['value']
        print(f'{display}')

    print(f'\nCurrent week\'s total hours: {green_string(seconds_to_formatted_hours(total_seconds_worked))}, {green_string(seconds_to_formatted_hours(total_seconds_worked_today))} today')


def process_action(action, date_time_obj=None):
    load_work_hours()
    # Call the appropriate method based on the user provided argument
    if date_time_obj is None:
        getattr(sys.modules[__name__], action)()
    else:
        getattr(sys.modules[__name__], action)(date_time_obj)


def display_status():
    if not WORK_HOURS or len(WORK_HOURS[0]) == 2:
        status_text = red_string('out')
    elif len(WORK_HOURS[0]) == 1:
        status_text = green_string('in')
    else:
        print(f'{red_string("Something went wrong")}')
        sys.exit()
    print(f'\nYou are currently punched {status_text}.')
    display_current_total()
    display_turn_in_total()


def main():
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    usage = f"Usage: {sys.argv[0]} -a <in | out | turn-in | current | status> [-d <YYYY-mm-dd HH:MM>]\n" \
        f"in                | i  - Punches you in if you haven\'t punched in already.\n" \
        f"out               | o  - Punches you out if you have already punched out.\n" \
        f"turn-in           | t  - Displays how many hours to turn in for last week.\n" \
        f"current           | c  - Displays how many hours accrued this week so far." \
        f"status            | s  - Displays whether or not you are punched in."

    date_time_obj = None
    if "-d" in opts:
        if len(args) == 2 and isinstance(args[1], str):
            date_time_obj = datetime.strptime(args[1], '%Y-%m-%d %H:%M')
        else:
            raise SystemExit(usage)
    if "-a" in opts:
        if any(arg in args for arg in ['in', 'i']):
            process_action("do_punch_in", date_time_obj)
        elif any(arg in args for arg in ['out', 'o']):
            process_action("do_punch_out", date_time_obj)
        elif any(arg in args for arg in ['turn-in', 't']):
            process_action("display_turn_in_total")
        elif any(arg in args for arg in ['current', 'c']):
            process_action("display_current_total")
        elif any(arg in args for arg in ['status', 's']):
            process_action("display_status")
        else:
            raise SystemExit(usage)
    else:
        raise SystemExit(usage)


main()
