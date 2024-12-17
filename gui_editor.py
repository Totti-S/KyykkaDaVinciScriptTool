import tkinter as tk
from tkinter import ttk
from itertools import product
import numpy as np
from editor import run_automatic_editor
import utils
from data_getter import get_data_from_api, Kyykkaliiga
import asyncio

setup_window = tk.Tk()
setup_window.title("Ottelun asetukset")
setup_window.minsize(450, 700)
setup_window.geometry('450x200+50+50')

game_data = None
# Thrower matrix: 2 rounds x 2 teams x 4 players x 4 throws + 1 name
thrower_data = np.empty((2,2,4,5), dtype=(np.str_, 32))
thrower_data[:] = ""

running_row = 0

def empty_name_data():
    for period, team, player in product(range(2), range(2), range(4)):
        t = int(not team)
        entries[period][t][player].set("")

def set_data_main_window(team_names: list[str], start_team: int):
    all_teams[0].set(team_names[0])
    all_teams[1].set(team_names[1])
    starting_team.set(start_team)

    # Insert data to entires in main window.
    for period, team, player in product(range(2), range(2), range(4)):
        entries[period][team][player].set(thrower_data[period][team][player][0])
    print(thrower_data)

def start_loading_data():
    global thrower_data
    path = utils.find_file()
    if path is None or path == '':
        data_loaded.set("Tiedosta ei valittu.")
        return
    print(path)
    return_values = utils.load_data(path)
    if isinstance(return_values, bool) and return_values is False:
        data_loaded.set("Datan lataus epäonnistui")
        return None

    thrower_data, team_names, start_team = return_values
    set_data_main_window(team_names, start_team)
    data_loaded.set('Data Ladattu tiedostosta')

def start_loading_from_api():
    global thrower_data
    if selected_value.get() == "OKL:n Sivuilta":
        liiga = Kyykkaliiga.OKL
    elif selected_value.get() == "NKL:n Sivuilta":
        liiga = Kyykkaliiga.NKL
    elif selected_value.get() == "Tre kyykkäliigan sivuilta":
        liiga = Kyykkaliiga.kyykkäliiga        
    else:
        return
    
    thrower_data, team_names, starting_team = asyncio.run(get_data_from_api(liiga, match_id=match_id.get(), year=year.get()))
    print("hei", thrower_data)
    if starting_team is None:
        starting_team = 0
    set_data_main_window(team_names, starting_team)
    data_loaded.set("Data Ladattu")



def combo_buttons(node):
    if selected_value.get() in ["Teksti tiedostosta", ""]:
        match_label.grid_forget()
        match_id_entry.grid_forget()
        year_label.grid_forget()
        year_entry.grid_forget()
        find_file_button.grid_forget()
        find_web_button.grid_forget()
    elif selected_value.get() == "OKL:n Sivuilta":
        year_label.grid(row=combo_row, column=2)
        year_entry.grid(row=combo_row+1, column=2)
    else:
        year_label.grid_forget()
        year_entry.grid_forget()

    if selected_value.get() not in ["Teksti tiedostosta", ""]:
        find_file_button.grid_forget()
        find_web_button.grid(row=combo_row+1, column=0)
        match_label.grid(row=combo_row, column=1)
        match_id_entry.grid(row=combo_row+1, column=1)
    else:
        find_file_button.grid(row=combo_row+1, column=0)
        find_web_button.grid_forget()

def get_missing_clips() -> list[int]:
    lista: list[list[int]] = []
    str_vars = [missing_clips1.get(), missing_clips2.get()]
    try:
        print(str_vars)
        for str_var in str_vars:
            print(lista)
            lista2 = []
            if "," in str_var:
                tmp = str_var.split(",") 
                for var in tmp:
                    if "-" in var:
                        tmp_2 = var.split('-')
                        for number in range(int(tmp_2[0])-1, int(tmp_2[1])):
                            lista2.append(number)
                    else:
                        lista2.append(int(var)-1)
            elif len(str_var):
                print("Olen täälä: ", str_var)
                if "-" in str_var:
                    tmp_2 = str_var.split('-')
                    for number in range(int(tmp_2[0])-1, int(tmp_2[1])):
                        lista2.append(number)
                else:
                    lista2.append(int(str_var)-1)
            lista.append(lista2)
    except IndexError:
        print("Tried to use '-' probably wrong. Format is : 'first_clip_missing'-'last_clip_missing'")
        print("WARN: Returning empty list as 'missing_clips' argument")
        return [[], []]
    except ValueError:
        print("Need to use only positive numbers, starting from 1!!!")
        print("WARN: Returning empty list as 'missing_clips' argument")
        return [[], []]
    return lista

def launch_program():
    if not names.get() and not points_var.get():
        status.set("Ei mitään valittu")
    else:

        missing = get_missing_clips()
        print(missing)
        status.set("")
        val = run_automatic_editor(
            start_offset=so_var.get(),
            middle_offset=mid_var.get(),
            starting_team=starting_team.get(),
            home_team=all_teams[0].get(),
            away_team=all_teams[1].get(),
            dublicate_timeline=copy_timeline_var.get(),
            add_names_to_clip=names.get(),
            add_score_to_clip=points_var.get(),
            thrower_data=thrower_data,
            points_direction=points_direction.get(),
            clips_missing_per_period=missing,
            fusion_app=app,
        )
        if val is True:
            status.set("Ohjelma ajoi onnistuneesti.")
        else:
            status.set("Ohjelmassa men jotain vikaan.")

def launch_saving():
    team = int(not starting_team.get())
    for period, i in product(range(2), range(16)):
        if i % 2 == 0:
            team = int(not team)
        if i < 8:
            player = i % 2 + 2 * (i // 4)
            thrower_data[period][team][player][0] = entries[period][team][player].get()
        else:
            player = i % 2 + 2 * ((i - 8) // 4)
            thrower_data[period][team][player][0] = entries[period][team][player].get()
    status.set("Nimi data tallennettu.")

def launch_saving_to_file():
    team_names = [
        all_teams[0].get(),
        all_teams[1].get(),
    ]
    utils.save_data(thrower_data, team_names, int(starting_team.get()))
            

def launch_points_window():
    row_idx = 0
    other_window = tk.Tk()
    other_window.title("Ottelun pisteet")
    other_window.minsize(700, 400)
    player_points = [
        [[], []],  # 1st round
        [[], []],  # 2nd round
    ]

    def make_period_entries(period: int, row_idx: int):
        ttk.Label(other_window, text=f"{period}. Erä").grid(row=row_idx, column=0)
        ttk.Label(other_window, text="Koti").grid(row=row_idx, column=3)
        ttk.Label(other_window, text="Vieras").grid(row=row_idx, column=10)
        row_idx += 1
        for row in range(1, 5):
            ttk.Label(other_window, text=f"{row}. Heittopaikka").grid(row=row_idx + row, column=0)
            player_var_array = []
            for col in range(1, 13):
                if col == 3 or col == 10:
                    continue
                elif 6 <= col <= 7:
                    ttk.Label(other_window, text="|").grid(row=row_idx + row, column=col)
                    continue
                string_var = tk.StringVar(other_window)
                ttk.Entry(other_window, textvariable=string_var, width=5, justify='center').grid(
                    row=row_idx + row, 
                    column=col,
                )
                player_var_array.append(string_var)
                if len(player_var_array) == 4:
                    team = col > 6
                    player_points[period - 1][team].append(player_var_array)
                    player_var_array = []
    

    make_period_entries(1, row_idx)
    row_idx += 6

    for col in range(13):
        if col == 3 or col == 10: 
            continue
        ttk.Label(other_window, text="------").grid(row=row_idx, column=col)
    row_idx += 1

    make_period_entries(2, row_idx)
    row_idx += 6

    for col in range(13):
        if col == 3 or col == 10: 
            continue
        ttk.Label(other_window, text="------").grid(row=row_idx, column=col)
    row_idx += 1

    def empty_fun():
        for period, team, player, throw in product(range(2), range(2), range(4), range(4)):
            player_points[period][team][player][throw].set("")

    def load_from_matrix():
        for period, team, player, throw in product(range(2), range(2), range(4), range(4)):
            player_points[period][team][player][throw].set(
                thrower_data[period][team][player][throw+1]
            )

    def save_to_matrix():
        for period, team, player, throw in product(range(2), range(2), range(4), range(4)):
            thrower_data[period][team][player][throw+1] = (
                player_points[period][team][player][throw].get()
            )
        saved_var.set("Data tallennettu!")

    # Initialize the entries
    print(thrower_data)
    load_from_matrix()
    
    ttk.Button(other_window, text="Tyhjennä", command=empty_fun).grid(row=row_idx, column=0)
    row_idx +=1
    ttk.Button(other_window, text="Lataa Data takaisin", command=load_from_matrix).grid(row=row_idx, column=0)
    row_idx +=1

    ttk.Button(other_window, text="Tallenna", command=save_to_matrix).grid(row=row_idx, column=0)
    saved_var = tk.StringVar(other_window, "")
    row_idx +=1
    ttk.Button(other_window, text="Sulje", command=lambda:other_window.destroy()).grid(row=row_idx, column=0)
    row_idx +=1
    tk.Label(other_window, textvariable=saved_var, fg='#0000FF').grid(row=row_idx, column=0)

def make_label_line(row_idx: int):
    ttk.Label(setup_window, text="-------------").grid(row=row_idx, column=0)
    ttk.Label(setup_window, text="-------------").grid(row=row_idx, column=1)
    ttk.Label(setup_window, text="-------------").grid(row=row_idx, column=2)

def make_entries(row_idx: int, round_no: int):
    ttk.Label(setup_window, text=f"{round_no}. Erä").grid(row=running_row, column=0)
    for j in range(1, 5):
        ttk.Label(setup_window, text=f"{j}. Heittopaikka").grid(row=running_row+j, column=0)
        for i in range(1, 3):
            entry_var = tk.StringVar(setup_window)
            ttk.Entry(setup_window, textvariable=entry_var, justify='center').grid(
                row=row_idx+j, column=i
            )
            entries[round_no-1][i-1].append(entry_var)


selected_value = tk.StringVar(setup_window)
combo = ttk.Combobox(setup_window, width=25, textvariable=selected_value, justify='center')
combo['values'] = (
    "Teksti tiedostosta",
    "OKL:n Sivuilta",
    "NKL:n Sivuilta",
    "Tre kyykkäliigan sivuilta", 
)
combo.grid(row=running_row, column=0)

match_label = ttk.Label(setup_window, text="Ottelu Id")
match_id = tk.IntVar(setup_window)
match_id_entry = ttk.Entry(setup_window, textvariable=match_id, width=5, justify='center')

year_label = ttk.Label(setup_window, text="Vuosi")
year = tk.IntVar(setup_window)
year_entry = ttk.Entry(setup_window, textvariable=year, width=5, justify='center')

combo.bind("<<ComboboxSelected>>", combo_buttons)
combo_row = running_row
running_row += 2

find_file_button = ttk.Button(setup_window, text="Lataa Tiedostosta", command=start_loading_data)
find_web_button = ttk.Button(setup_window, text="Lataa Sivulta", command=start_loading_from_api)
running_row += 1

data_loaded = tk.StringVar(setup_window)
ttk.Label(setup_window, textvariable=data_loaded).grid(row=running_row, column=0)
running_row += 1

ttk.Label(setup_window, text="Koti").grid(row=running_row, column=1)
ttk.Label(setup_window, text="Vieras").grid(row=running_row, column=2)
running_row += 1

all_teams = [tk.StringVar(setup_window), tk.StringVar(setup_window)]
ttk.Label(setup_window, text="Joukkue nimet").grid(row=running_row, column=0)
ttk.Entry(setup_window, textvariable=all_teams[0], justify='center').grid(row=running_row, column=1)
ttk.Entry(setup_window, textvariable=all_teams[1], justify='center').grid(row=running_row, column=2)
running_row += 1

make_label_line(running_row)
running_row += 1

entries = [
    [[], []], # 1st period
    [[], []], # 2nd period
]

# Add the 1. period entires
make_entries(running_row, 1)
running_row += 4 + 1   # Add the entires and proceed to next empty row 

tk.Label(setup_window, text="1. Erän aloittaja").grid(row=running_row, column=0)
starting_team = tk.BooleanVar(setup_window, value=False)
ttk.Radiobutton(
    setup_window, 
    text="",
    variable=starting_team,
    value=False, 
).grid(row=running_row, column=1)
ttk.Radiobutton(
    setup_window, 
    text="",
    variable=starting_team,
    value=True, 
).grid(row=running_row, column=2)
running_row += 1

# Add one empty row to make separation between the periods
make_label_line(running_row)
running_row += 1

# Add the 2. period entires
make_entries(running_row, 2)
running_row += 4 + 1   # Add the entires and proceed to next empty row 

# Add one empty row to make separation between the periods
make_label_line(running_row)
running_row += 1

names = tk.BooleanVar(setup_window, value=True)
points_var = tk.BooleanVar(setup_window, value=False)
ttk.Checkbutton(
    setup_window, 
    text="Nimet",
    variable=names,
    onvalue=True, 
    offvalue=False
).grid(row=running_row, column=0)
ttk.Checkbutton(
    setup_window, 
    text="Pisteet",
    variable=points_var,
    onvalue=True, 
    offvalue=False,
).grid(row=running_row, column=1)
running_row += 1

copy_timeline_var = tk.BooleanVar(setup_window, True)
ttk.Checkbutton(
    setup_window, 
    text="Kopio aikajana",
    variable=copy_timeline_var,
    onvalue=True, 
    offvalue=False,
).grid(row=running_row, column=0)
running_row += 1

so_var = tk.IntVar(value=1)
ttk.Label(setup_window, text="Alkuklippien määrä").grid(row=running_row, column=0)
tk.Scale(setup_window, variable=so_var, orient="horizontal", from_=0, to=10, tickinterval=5).grid(
    row=running_row,
    column=1,
)
running_row += 1
mid_var = tk.IntVar(value=1)
ttk.Label(setup_window, text="Keskiklippien määrä").grid(row=running_row, column=0)
tk.Scale(setup_window, variable=mid_var, orient="horizontal", from_=0, to=10, tickinterval=5).grid(
    row=running_row,
    column=1,
)
running_row += 1

missing_clips1 = tk.StringVar(setup_window)
ttk.Label(setup_window, text="Puuttuvat klipit 1. erä").grid(row=running_row, column=0)
ttk.Entry(setup_window, textvariable=missing_clips1, justify='left').grid(
    row=running_row, column=1
)
running_row += 1

missing_clips2 = tk.StringVar(setup_window)
ttk.Label(setup_window, text="Puuttuvat klipit 2. erä").grid(row=running_row, column=0)
ttk.Entry(setup_window, textvariable=missing_clips2, justify='left').grid(
    row=running_row, column=1
)
running_row += 1

ttk.Button(setup_window, text="Pisteet", command=launch_points_window).grid(
    row=running_row,
    column=0,
)
running_row += 1

tk.Label(setup_window, text="Mailoja yli:").grid(row=running_row, column=0)
points_direction = tk.BooleanVar(setup_window, value=True)
ttk.Radiobutton(
    setup_window, 
    text="Positiivinen",
    variable=points_direction,
    value=True, 
).grid(row=running_row, column=1)
ttk.Radiobutton(
    setup_window, 
    text="Negatiivinen",
    variable=points_direction,
    value=False, 
).grid(row=running_row, column=2)
running_row += 1


ttk.Button(setup_window, text="Tallenna nimi data", command=launch_saving).grid(
    row=running_row,
    column=0,
)
ttk.Button(setup_window, text="Tyhjennä nimi data", command=empty_name_data).grid(
    row=running_row,
    column=1,
)
running_row += 1

ttk.Button(setup_window, text="Tallenna data tiedostoon", command=launch_saving_to_file).grid(
    row=running_row,
    column=0,
)
running_row += 1

ttk.Button(setup_window, text="Aloita ohjelma", command=launch_program).grid(
    row=running_row,
    column=0,
)
ttk.Button(setup_window, text="Poistu", command=lambda:setup_window.destroy()).grid(
    row=running_row,
    column=1
)
running_row += 1

status = tk.StringVar(setup_window)
tk.Label(setup_window, textvariable=status, fg='#0000FF').grid(
    row=running_row,
    column=0,
)
running_row += 1

setup_window.mainloop()