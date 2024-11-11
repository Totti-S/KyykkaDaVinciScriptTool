import numpy as np
import tkinter as tk
import tkinter.filedialog as filedialog

def find_file() -> str:
    tk.Tk().withdraw() # prevents an empty tkinter window from appearing
    path = filedialog.askopenfilename()
    return path

def ask_filename() -> str:
    tk.Tk().withdraw() # prevents an empty tkinter window from appearing
    path = filedialog.asksaveasfilename()
    return path
    
def load_data(file_path: str) -> tuple[np.ndarray[np.str_], np.ndarray[np.str_], tuple[str, str], bool] | bool:
    game_data = None
    # Thrower matrix: 2 rounds x 2 teams x 4 players x 4 throws + 1 name
    thrower_data = np.empty((2,2,4,5), dtype=(np.str_, 32))
    thrower_data[:] = ""
    starting_team = False
    try:
        with open(file_path, 'r', encoding='utf-8') as file: 
            game_data = file.readlines()
            game_data = [t.rstrip('\n') for t in game_data]
            
            # First line optionally can be header
            if game_data[0][0] == '#':
                data = game_data.pop(0)[1:]
                home_team, away_team, starter, *other = data.split(";")
                if (tmp := starter.lower()) == 'home' or tmp == 'koti':
                    starting_team = False
                elif tmp == 'away' or tmp == 'vieras':
                    starting_team = True
                elif tmp == home_team.lower():
                    starting_team = False
                elif tmp == away_team.lower():
                    starting_team = True
            
            def parse_and_save_data(current_team: int, data: list[str], period: int) -> None:
                for i, line in enumerate(data):
                    if line[0] == '#':
                        break
                    name, throw1, throw2 = line.split(';')
                    if i < 8:
                        player_idx = i % 2 + 2 * (i // 4)
                        thrower_data[period][current_team][player_idx][0] = name
                        thrower_data[period][current_team][player_idx][1] = throw1
                        thrower_data[period][current_team][player_idx][2] = throw2
                    else:
                        player_idx = i % 2 + 2 * ((i - 8) // 4)
                        thrower_data[period][current_team][player_idx][3] = throw1
                        thrower_data[period][current_team][player_idx][4] = throw2
                    if i % 2:
                        current_team = int(not current_team)
            
            # First period
            start_team = int(starting_team)
            parse_and_save_data(start_team, game_data, 0)
            # Second period
            rest_of_throws = game_data[game_data.index('#')+1:]
            start_team = int(not starting_team)
            parse_and_save_data(start_team, rest_of_throws, 1)
        return thrower_data, (home_team, away_team), int(starting_team)
    except Exception as e:
        print(f"Jotain meni pieleen: {e}")
        return False
    
if __name__ == '__main__':
    j = load_data("E:/kyykkavids/Leikkaamattomat/testi.txt")
    print(j)