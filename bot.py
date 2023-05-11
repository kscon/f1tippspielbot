import logging
import pandas as pd
import datetime
from os.path import exists
from telegram.ext import Updater, CommandHandler, Filters
from apikey import API_KEY

logging.basicConfig(
    # filename='wgbot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

filepath_race_data = 'race_data/'
filepath_data = 'data/'


def test(update, context):
    # Send a message when the command /test is issued
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hi!')


def read_guesses(racename):
    return pd.read_csv(filepath_race_data + racename + '.csv', delimiter=';')


def read_results(racename):
    return pd.read_csv(filepath_race_data + racename + '_results.csv', delimiter=';')


def read_races():
    return pd.read_csv(filepath_data + 'races.csv', delimiter=';')


def read_drivers():
    return pd.read_csv(filepath_data + 'drivers.csv', delimiter=';')


def read_standings():
    return pd.read_csv(filepath_data + 'standings.csv', delimiter=';')


def print_standings(update, context):
    df = read_standings()
    context.bot.send_message(chat_id=update.effective_chat.id, text=df.to_string(index=False))


def print_overall_points(update, context):
    df = read_standings()

    output = ''
    for c in df.columns.to_list():
        if check_name_valid(c):
            sum = df[c].sum()
            output += c + ' ' + str(sum) + '\n'

    # df = df.sum(axis=0)
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)


def print_drivers(update, context):
    df = read_drivers()
    context.bot.send_message(chat_id=update.effective_chat.id, text=df.to_string(index=False))


def print_races(update, context):
    df = read_races()
    context.bot.send_message(chat_id=update.effective_chat.id, text=df.to_string(index=False))


def print_guess(update, context):
    try:
        racename = context.args[0]
        df = read_guesses(racename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid racename')
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text=racename + ":")
    context.bot.send_message(chat_id=update.effective_chat.id, text=df.to_string(index=False))


def print_results(update, context):
    racename = context.args[0]
    df = read_results(racename)
    context.bot.send_message(chat_id=update.effective_chat.id, text=df.to_string(index=False))


# format of command:
# /record_guess <name> <racename> <mode> <1.driver> <2.driver> <3.driver> ...
def record_guess(update, context):
    try:
        name = str(context.args[0]).lower()
        if not check_name_valid(name):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Not a valid name')
            return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid name')
        return

    # check for valid race
    try:
        df_races = read_races()
        racename = str(context.args[1]).lower()
        if racename not in df_races.races.to_list():
            context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Not a valid racename')
            return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid racename')
        return

    # check if mode is correct
    try:
        mode = context.args[2]
        if not (mode is 'Q' or mode is 'R'):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid mode (Race or Qualy)')
            return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid mode (Race or Qualy)')
        return

    # check drivers
    try:
        length = len(context.args)
        length -= 3

        if (mode == 'Q' and length != 3) or (mode == 'R' and length != 5):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter 3 Drivers for Q and 5 for R')
            return

        driver_guesses = context.args[3:]

        # check for valid driver
        for guess in driver_guesses:
            # number = int(guess.split('.')[0])
            driver = guess.split('.')[1]
            if not check_driver_valid(driver):
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Error: ' + driver + ' is not a valid driver')
                return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Error: Enter valid drivers')

    # guess is valid
    write_guesses(context, update, name, racename, mode, driver_guesses)


def write_guesses(context, update, name, racename, mode, guesses):
    try:
        df_guesses = read_guesses(racename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Error: Could not find CSV File for ' + racename)
        return

    drivers = []
    # places = []
    # modes = [mode for guess in guesses]
    for guess in guesses:
        driver = guess.split('.')[1].upper()
        try:
            place = int(guess.split('.')[0])
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Error: Driver ' + driver + ' has not a valid position guess!')
        drivers.append(driver)
        # places.append(place)

    # assume we have a sorted drivers guess list
    # update dataframe by guesses.

    if mode == 'Q':
        df_guesses.loc[0:2, name] = drivers
    else:

        df_guesses.loc[3:, name] = drivers

    df_guesses.to_csv(filepath_race_data + racename + '.csv', sep=';', index=False)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Guess successfully added!")


# format of command:
# record_results <racename> <mode> <1.driver> <2.driver> <3.driver> ...
def record_results(update, context):
    # check for valid race
    try:
        df_races = read_races()
        racename = str(context.args[0]).lower()
        if racename not in df_races.races.to_list():
            context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Not a valid racename')
            return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid racename')
        return

    # check if mode is correct
    try:
        mode = context.args[1]
        if not (mode is 'Q' or mode is 'R'):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid mode (Race or Qualy)')
            return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a valid mode (Race or Qualy)')
        return

    # check drivers
    try:
        length = len(context.args)
        length -= 2

        if (mode == 'Q' and length < 3) or (mode == 'R' and length < 5):
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Error: Enter 3 Drivers for Q and min. 5 for R')
            return

        driver_placement = context.args[2:]

        # check for valid driver
        for data in driver_placement:
            # number = int(guess.split('.')[0])
            driver = data.split('.')[1]
            if not check_driver_valid(driver):
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text='Error: ' + driver + ' is not a valid driver')
                return
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Error: Enter valid drivers')

    write_results(update, context, racename, mode, driver_placement)


def write_results(update, context, racename, mode, placement):
    try:
        df_results = read_results(racename)
    except:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Error: Could not find result CSV File for ' + racename)
        return

    drivers = []
    places = []

    # modes = [mode for guess in guesses]
    for data in placement:
        driver = data.split('.')[1].upper()
        try:
            place = int(data.split('.')[0])
        except:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Error: Driver ' + driver + ' has not a valid position!')
        places.append(place)
        drivers.append(driver)
        # places.append(place)

    # driver_place_pair = zip(places, drivers)

    # assume we have a sorted drivers guess list
    # update dataframe by guesses.

    df_results = df_results[df_results['mode'] != mode]

    df_results = df_results.append(pd.DataFrame({'mode': [mode for d in drivers],
                                                 'place': places,
                                                 'driver': drivers}), ignore_index=True)

    df_results.to_csv(filepath_race_data + racename + '_results.csv', sep=';', index=False)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Results successfully added!")


# adds a new race.csv and a race_results.csv
def add_new_race(update, context):
    df_races = read_races()
    try:
        racename = context.args[0]
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Enter a racename!')
        return

    flag = 0

    try:
        if context.args[1] == 'f':
            flag = 1
    except:
        flag = 0

    if racename not in df_races['races'].to_list():
        context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Racename does not exist!')
        return

    modes = ['Q', 'Q', 'Q', 'R', 'R', 'R', 'R', 'R']
    places = [1, 2, 3, 1, 2, 3, 4, 5]
    driver = ['-' for l in range(len(places))]
    df_guesses_template = pd.DataFrame({'mode': modes, 'place': places})

    df_results_template = pd.DataFrame({'mode': modes, 'place': places, 'driver': driver})

    names = get_list_of_names()
    for name in names:
        df_guesses_template[name] = ['-' for n in range(8)]

    if not exists(filepath_race_data + racename + '.csv') or flag:
        df_guesses_template.to_csv(filepath_race_data + racename + '.csv', index=False, sep=';')
        df_results_template.to_csv(filepath_race_data + racename + '_results.csv', index=False, sep=';')
        context.bot.send_message(chat_id=update.effective_chat.id, text='Race data was successfully created')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Race already exists! If you want to overwrite existing data, add \" f \" to the command')


def get_list_of_names():
    with open('listofnames.txt', 'r') as f:
        name_list = f.read().strip().split()
    return name_list


def check_name_valid(name):
    name_list = get_list_of_names()
    if name in name_list:
        return True
    else:
        return False


def check_driver_valid(driver: str):
    driver = driver.upper()
    df_drivers = read_drivers()

    if driver in df_drivers.drivertag.to_list():
        return True
    else:
        return False


# calculate all the points
def calculate_standings(update, context):
    races = read_races()['races'].tolist()
    df_standings = read_standings()

    for race in races:
        if exists(filepath_race_data + race + '.csv'):
            names = get_list_of_names()
            df_guess = read_guesses(race)
            df_results = read_results(race)

            for name in names:
                points = 0
                for index, row in df_guess.iterrows():
                    driver = row[name]
                    place_guess = int(row['place'])
                    mode = row['mode']

                    if driver == '-' or df_results[(df_results['mode'] == mode)]['driver'].to_list()[0] == '-':
                        continue

                    place_result = \
                    df_results[(df_results['mode'] == mode) & (df_results['driver'] == driver)]['place'].to_list()[0]

                    diff = abs(place_result - place_guess)

                    if diff > 5:
                        diff = 5

                    if place_result == -1:
                        diff = 3

                    points += diff
                df_standings.loc[df_standings['race'] == race, name] = points

    df_standings.to_csv(filepath_data + 'standings.csv', index=False, sep=';')
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Successfully updated the standings!')

    # context.bot.send_message(chat_id=update.effective_chat.id,
    #                             text='Something went wrong while calculating current standings')


def print_help(update, context):
    output = 'List of commands:\n'
    output = output + '/print_guess => print guesses of a race. Usage: /print_guess <racename> \n'
    output = output + '/print_results => print results of a race. Usage: /print_results <racename> \n'
    output = output + '/print_drivers => print list of drivers\n'
    output = output + '/print_races => print list of races\n'
    output = output + '/print_standings => print table of points for guessing game\n'
    output = output + '/print_overall_points => print table of summed up points\n'
    output = output + '/calculate_standings => calculate points of guessing game. Use after entering race results\n'
    output = output + '/record_guess => record a guess for a race. Use Q for Quali and R for race. Usage: /record_guess <name> <racename> <Q||R> <1.drivertag> <2.drivertag> <3.drivertag> ...\n\n'
    output = output + '/record_results => record results for a race. Usage: /record_results <racename> <Q||R> <1.drivertag> <2.drivertag> <3.drivertag> ...\n\n'
    output = output + '/new_race => create data for a new race. Use only on a raceweekend and only one race in advance. Usage: /new_race <racename>\n\n'
    context.bot.send_message(chat_id=update.effective_chat.id, text=output)
    logger.info('help was issued')


def debug(update, context):
    print(str(update.effective_chat.id))
    #context.bot.send_message(chat_id=update.effective_chat.id, text=str(update.effective_chat.id))


def main():
    # initialize stuff
    updater = Updater(API_KEY, use_context=True)
    jq = updater.job_queue

    # introduce dispatcher locally
    dp = updater.dispatcher

    chat_ids_all = []
    with open('chatids_all.txt', 'r') as f:
        text = f.read().strip().split()
        for t in text:
            chat_ids_all.append(int(t))

    # filter = Filters.chat(chat_id=chat_ids)
    filter_all = Filters.chat(chat_id=chat_ids_all)
    # dp.add_handler(CommandHandler("test", test, filter_all))
    #dp.add_handler(CommandHandler("debug", debug)
    dp.add_handler(CommandHandler("help", print_help, filter_all))
    dp.add_handler(CommandHandler("print_guess", print_guess, filter_all))
    dp.add_handler(CommandHandler("print_results", print_results, filter_all))
    dp.add_handler(CommandHandler("print_drivers", print_drivers, filter_all))
    dp.add_handler(CommandHandler("print_races", print_races, filter_all))
    dp.add_handler(CommandHandler("print_standings", print_standings, filter_all))
    dp.add_handler(CommandHandler("print_overall_points", print_overall_points, filter_all))
    dp.add_handler(CommandHandler("record_guess", record_guess, filter_all))
    dp.add_handler(CommandHandler("record_results", record_results, filter_all))
    dp.add_handler(CommandHandler("calculate_standings", calculate_standings, filter_all))
    dp.add_handler(CommandHandler("new_race", add_new_race, filter_all))

    logger.info("Started bot")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
