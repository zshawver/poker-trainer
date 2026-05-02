
from positions import Positions

def createOpenRaiseRanges():
    # Initialize the outer dictionary
    openRaise = {}

    # Define ranges for each table size
    for table_size, positions in Positions.items():
        table_ranges = {}
        for position in positions:
            table_ranges[position] = []

        if table_size == 3:
            table_ranges['BTN'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
                'AKo', 'KK', 'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'K6s', 'K5s', 'K4s', 'K3s', 'K2s',
                'AQo', 'KQo', 'QQ', 'QJs', 'QTs', 'Q9s', 'Q8s', 'Q7s',
                'AJo', 'KJo', 'QJo', 'JJ', 'JTs', 'J9s', 'J8s', 'J7s',
                'ATo', 'KTo', 'QTo', 'JTo', 'TT', 'T9s', 'T8s', 'T7s',
                'A9o', 'K9o', 'Q9o', 'J9o', 'T9o', '99', '98s', '97s', '96s',
                'A8o', 'K8o', 'Q8o', 'J8o', 'T8o', '98o', '88', '87s', '86s', '87o',
                '77', '76s', '75s', '76o', '66', '65s', '64s', '65o', '55', '54s', '53s', '44', '43s', '33', '22',
                'A7o', 'K7o', 'A6o', 'K6o', 'A5o', 'K5o', 'A4o', 'A3o', 'A2o'
            ]
            table_ranges['SB'] = table_ranges['BTN']
            table_ranges['BB'] = table_ranges['BTN']

        elif table_size == 4:
            table_ranges['BTN'] = openRaise[3]['BTN']
            table_ranges['SB'] = openRaise[3]['SB']
            table_ranges['BB'] = openRaise[3]['BB']
            table_ranges['UTG'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs',
                'AKo', 'KK', 'KQs',
                'AQo', 'KQo', 'QQ', 'QJs',
                'AJo', 'JJ', 'JTs',
                'ATo', 'TT', 'T9s', '99', '98s',
                '88', '87s', '77', '76s',
                '66', '55', '44', '33', '22'
            ]

        elif table_size == 5:
            table_ranges['BTN'] = openRaise[3]['BTN']
            table_ranges['SB'] = openRaise[3]['SB']
            table_ranges['BB'] = openRaise[3]['BB']
            table_ranges['UTG'] = openRaise[4]['UTG']
            table_ranges['CO'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s',
                'AKo', 'KK', 'KQs', 'KJs',
                'AQo', 'KQo', 'QQ', 'QJs',
                'AJo', 'KJo', 'QJo', 'JJ', 'JTs',
                'ATo', 'KTo', 'QTo', 'JTo', 'TT', 'T9s',
                'A9o', 'K9o', 'Q9o', 'J9o', '99', '98s',
                'A8o', 'K8o', 'Q8o', '88', '87s', '77', '76s',
                '66', '65s', '64s', '55', '54s', '44', '33', '22'
            ]

        elif table_size == 6:
            table_ranges['BTN'] = openRaise[3]['BTN']
            table_ranges['SB'] = openRaise[3]['SB']
            table_ranges['BB'] = openRaise[3]['BB']
            table_ranges['UTG'] = openRaise[4]['UTG']
            table_ranges['HJ'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s',
                'AKo', 'KK', 'KQs', 'KJs',
                'AQo', 'KQo', 'QQ', 'QJs',
                'AJo', 'KJo', 'QJo', 'JJ', 'JTs',
                'ATo', 'KTo', 'QTo', 'JTo', 'TT', 'T9s',
                'A9o', 'K9o', 'Q9o', 'J9o', '99', '98s',
                'A8o', 'K8o', 'Q8o', '88', '87s', '77', '76s',
                '66', '65s', '64s', '55', '54s', '44', '33', '22'
            ]
            table_ranges['CO'] = openRaise[5]['CO']

        elif table_size == 7:
            table_ranges['BTN'] = openRaise[3]['BTN']
            table_ranges['SB'] = openRaise[3]['SB']
            table_ranges['BB'] = openRaise[3]['BB']
            table_ranges['UTG'] = openRaise[4]['UTG']
            table_ranges['LJ'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s',
                'AKo', 'KK', 'KQs', 'KJs',
                'AQo', 'KQo', 'QQ', 'QJs',
                'AJo', 'KJo', 'QJo', 'JJ', 'JTs',
                'ATo', 'KTo', 'QTo', 'JTo', 'TT', 'T9s',
                'A9o', 'K9o', 'Q9o', 'J9o', '99', '98s',
                'A8o', 'K8o', 'Q8o', '88', '87s', '77', '76s',
                '66', '65s', '64s', '55', '54s', '44', '33', '22'
            ]
            table_ranges['HJ'] = openRaise[6]['HJ']
            table_ranges['CO'] = openRaise[5]['CO']

        elif table_size == 8:
            table_ranges['BTN'] = openRaise[3]['BTN']
            table_ranges['SB'] = openRaise[3]['SB']
            table_ranges['BB'] = openRaise[3]['BB']
            table_ranges['UTG'] = openRaise[4]['UTG']
            table_ranges['UTG+1'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s',
                'AKo', 'KK', 'KQs', 'KJs',
                'AQo', 'KQo', 'QQ', 'QJs',
                'AJo', 'KJo', 'QJo', 'JJ', 'JTs',
                'ATo', 'KTo', 'QTo', 'JTo', 'TT', 'T9s',
                'A9o', 'K9o', 'Q9o', 'J9o', '99', '98s',
                'A8o', 'K8o', 'Q8o', '88', '87s', '77', '76s',
                '66', '65s', '64s', '55', '54s', '44', '33', '22'
            ]
            table_ranges['LJ'] = openRaise[7]['LJ']
            table_ranges['HJ'] = openRaise[6]['HJ']
            table_ranges['CO'] = openRaise[5]['CO']

        elif table_size == 9:
            table_ranges['BTN'] = openRaise[3]['BTN']
            table_ranges['SB'] = openRaise[3]['SB']
            table_ranges['BB'] = openRaise[3]['BB']
            table_ranges['UTG'] = openRaise[4]['UTG']
            table_ranges['UTG+1'] = openRaise[8]['UTG+1']
            table_ranges['UTG+2'] = [
                'AA', 'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s',
                'AKo', 'KK', 'KQs', 'KJs',
                'AQo', 'KQo', 'QQ', 'QJs',
                'AJo', 'KJo', 'QJo', 'JJ', 'JTs',
                'ATo', 'KTo', 'QTo', 'JTo', 'TT', 'T9s',
                'A9o', 'K9o', 'Q9o', 'J9o', '99', '98s',
                'A8o', 'K8o', 'Q8o', '88', '87s', '77', '76s',
                '66', '65s', '64s', '55', '54s', '44', '33', '22'
            ]
            table_ranges['LJ'] = openRaise[7]['LJ']
            table_ranges['HJ'] = openRaise[6]['HJ']
            table_ranges['CO'] = openRaise[5]['CO']

        openRaise[table_size] = table_ranges
    return openRaise

openRaise = createOpenRaiseRanges()
