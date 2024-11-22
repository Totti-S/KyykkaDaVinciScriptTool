from enum import Enum, auto
import requests
import asyncio
import pandas as pd
import numpy as np
import re

class Kyykkaliiga(Enum):
    NKL = auto()
    kyykkäliiga = auto()
    OKL = auto()

async def get_data_from_api(liiga: Kyykkaliiga, match_id: int, year: int = 2024):
    thrower_data = np.empty((2,2,4,5), dtype=(np.str_, 32))
    thrower_data[:] = ""
    team_names = []
    starting_team = None

    print(liiga, liiga == Kyykkaliiga.OKL)
    loop = asyncio.get_event_loop()
    if liiga == Kyykkaliiga.NKL:
        api_url = f"https://kyykka.com/api/matches/{match_id}"
        response = await loop.run_in_executor(None, requests.get, api_url)
        data = response.json()
        team_names.append(data['home_team']['current_abbreviation'])
        team_names.append(data['away_team']['current_abbreviation'])
        for period, p_name in enumerate(['first', 'second']):
            for team, t_name in enumerate(['home', 'away']):
                players = data[f'{p_name}_round'][t_name]
                for player in players:
                    turn = player['throw_turn']
                    turn -= 1
                    thrower_data[period][team][turn][0] = player['player']['player_name']
                    for throw, th_name in enumerate(['first', 'second', 'third', 'fourth'], 1):
                        # NKL has data in a points times 2
                        score = player[f'score_{th_name}']
                        if score not in ['h', 'e']:
                            score = str(int(score) *2)
                        thrower_data[period][team][turn][throw] = score

    elif liiga == Kyykkaliiga.OKL:
        api_url = f"https://www.oamkry.fi/tilastot/a-{year-1}-{year}/pelin_tilasto.php?pelinro={match_id}"
        response = await loop.run_in_executor(None, requests.get, api_url)
        list_of_df = pd.read_html(response.text, encoding='utf-8')
        period = None
        last_team = 1
        last_team_name = None
        i = 0
        for row in list_of_df[1].iterrows():
            name, st, nd, rd, th, *other = row[1]
            if name == "1. Erä":
                period = 0
                continue
            elif name == "2. Erä":
                period = 1
                continue
            elif name == "Lopputulos":
                break
            if i >= 16:
                i -= 16
            if i < 8:
                player = i % 2 + 2 * (i // 4)
            else:
                player = i % 2 + 2 * ((i - 8) // 4)
            name, team = name.split(", ")
            if last_team_name != team:
                last_team = int(not last_team)
                last_team_name = team
                if len(team_names) < 2:
                    team_names.append(last_team_name)
            thrower_data[period][last_team][player] = [name, st, nd, rd, th]
            i += 1

    elif liiga == Kyykkaliiga.kyykkäliiga:
        api_url = f"https://kyykkaliiga.fi/tilastot/ottelu/{match_id}"
        response = await loop.run_in_executor(None, requests.get, api_url)
        # Kyykkaliiga does not spefically have home or away.
        # Assume home is the first one.
        data = response.text.split('h2')
        header = None
        for line in data:
            if "&ndash;" in line:
                header = line
                break
        home, away, *other = re.findall(r'(\(.*\))', header)
        home = home.rstrip(')').lstrip('(')
        away = away.rstrip(')').lstrip('(')
        team_names.append(home)
        team_names.append(away)
        list_of_df = pd.read_html(response.text, encoding='utf-8')
        period = None
        last_team = 0
        starting_team = None
        i = 0
        for row in list_of_df[0].iterrows():
            name, st, nd, _, rd, th, *other = row[1]
            if name == "1.Erä":
                period = 0
                continue
            if "Erän tulos" in name:
                continue
            elif name == "2.Erä":
                print(thrower_data)
                period = 1
                continue
            elif name == "Ottelun tulos":
                break
            if i < 8:
                player = i % 2 + 2 * (i // 4)
            else:
                player = i % 2 + 2 * ((i - 8) // 4)
            name, team = name.split(", ")
            if team in home:
                last_team = 0
            elif team in away:
                last_team = 1
            if starting_team is None:
                starting_team = last_team
            thrower_data[period][last_team][player] = [name, st, nd, rd, th]
            i += 1

    return thrower_data, team_names, starting_team

if __name__ == '__main__':
    print('Hello')
    # asyncio.run(get_data_from_api(Kyykkaliiga.kyykkäliiga, 5197))
    jotain = asyncio.run(get_data_from_api(Kyykkaliiga.OKL, 93, 2023))
    print(jotain[0])