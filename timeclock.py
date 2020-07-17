#! /usr/bin/python3

# A simple time-clock program to keep track of hours.

import sys
import os
import csv
from datetime import datetime, time, timedelta
from colorama import Fore, Style
from pathlib import Path

# The data file holding punch-ins and outs.  Data is stored newest to oldest.
DATA_FILE = str(Path.home()) + '/timeclock.csv'
DATETIME_STRING_FORMAT = "%B %d, %Y %H:%M:%S"
NOW = datetime.now()
WORK_HOURS = []


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
    # Write the hourly data to the csv file.
    with open(DATA_FILE, mode='w+') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(WORK_HOURS)


def display_success(action):
    print('Punched you ' + Fore.GREEN + action + Style.RESET_ALL + f': {NOW.strftime(DATETIME_STRING_FORMAT)}')


def punch_in():
    # Punch in if there is no dangling punch in already existing.
    # We always work with the first element in the list.
    if not WORK_HOURS or len(WORK_HOURS[0]) == 2:
        WORK_HOURS.insert(0, [NOW.timestamp()])
        write_hour_data()
        display_success('in')
        current_total()
    elif len(WORK_HOURS[0]) == 1:
        print(Fore.RED + 'Error. ' + Style.RESET_ALL + 'You have already punched in, you need to punch out first.')
        sys.exit()
    else:
        print(Fore.RED + 'Something went wrong punching you in.' + Style.RESET_ALL)


def punch_out():
    # Punch out only if there is a dangling punch in.
    # We always work with the first element in the list.
    if not WORK_HOURS or len(WORK_HOURS[0]) == 2:
        print(Fore.RED + 'Error.  ' + Style.RESET_ALL + 'You have already punched out, you need to punch in first.')
        sys.exit()
    elif len(WORK_HOURS[0]) == 1:
        WORK_HOURS[0] = [WORK_HOURS[0][0], NOW.timestamp()]
        write_hour_data()
        display_success('out')
        current_total()
    else:
        print(Fore.RED + 'Something went wrong punching you out.' + Style.RESET_ALL)


def turn_in_total():
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

    print(f'Total hours to turn in for last week: ' + Fore.GREEN + f'{total_seconds_worked / 3600:.2f}' + Style.RESET_ALL)


def current_total():
    # This past Monday at midnight
    start_of_current_week = datetime.combine(NOW - timedelta(days=NOW.weekday()), time())
    start_of_current_day = datetime.combine(NOW - timedelta(0), time())
    total_seconds_worked = 0
    total_seconds_worked_today = 0

    # Calculate the current week's hours.
    for entry in WORK_HOURS:
        check_in = float(entry[0])
        if len(entry) == 2:
            if check_in >= start_of_current_week.timestamp():
                total_seconds_worked += (float(entry[1]) - check_in)
            if check_in >= start_of_current_day.timestamp():
                total_seconds_worked_today += (float(entry[1]) - check_in)
        elif len(entry) == 1:
            total_seconds_worked += (NOW.timestamp() - check_in)
            total_seconds_worked_today += (NOW.timestamp() - check_in)

    print(f'Current week\'s total hours: ' + Fore.GREEN + f'{total_seconds_worked / 3600:.2f}' + Style.RESET_ALL + ', ' +
          Fore.GREEN + f'{total_seconds_worked_today / 3600:.2f}' + Style.RESET_ALL + ' today')


def process_action(function):
    load_work_hours()
    # Call the appropriate method based on the user provided argument
    getattr(sys.modules[__name__], function)()


def status():
    if not WORK_HOURS or len(WORK_HOURS[0]) == 2:
        status_text = Fore.RED + 'out' + Style.RESET_ALL
    elif len(WORK_HOURS[0]) == 1:
        status_text = Fore.GREEN + 'in' + Style.RESET_ALL
    else:
        print(Fore.RED + 'Something went wrong' + Style.RESET_ALL)
        sys.exit()
    print(f'You are currently punched {status_text}.')
    current_total()
    turn_in_total()


def main():
    # TODO: add the ability to pass in a custom datetime from cli for in/out

    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    usage = f"Usage: {sys.argv[0]} -a <in | out | turn-in | current | status>.\n" \
        f"in      | i  - Punches you in if you haven\'t punched in already.\n" \
        f"out     | o  - Punches you out if you have already punched in.\n" \ 
        f"turn-in | t  - Displays how many hours to turn in for last week.\n" \ 
        f"current | c  - Displays how many hours accrued this week so far." \
        f"status  | s  - Displays whether or not you are punched in."

    if "-a" in opts:
        if any(arg in args for arg in ['in', 'i']):
            process_action("punch_in")
        elif any(arg in args for arg in ['out', 'o']):
            process_action("punch_out")
        elif any(arg in args for arg in ['turn-in', 't']):
            process_action("turn_in_total")
        elif any(arg in args for arg in ['current', 'c']):
            process_action("current_total")
        elif any(arg in args for arg in ['status', 's']):
            process_action("status")
        else:
            raise SystemExit(usage)
    else:
        raise SystemExit(usage)


main()

