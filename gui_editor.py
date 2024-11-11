import tkinter as tk
from tkinter import ttk
import numpy as np
from editor import run_automatic_editor
from utils import load_data, find_file

setup_window = tk.Tk()
setup_window.title("Ottelun asetukset")
setup_window.minsize(400, 700)
setup_window.geometry('450x200+50+50')

game_data = None
# Thrower matrix: 2 rounds x 2 teams x 4 players x 4 throws + 1 name
thrower_data = np.empty((2,2,4,5), dtype=(np.str_, 32))
thrower_data[:] = ""

running_row = 0

def start_finding_file():
    path = find_file()
    file_path.set(path)
    if game_data is not None:
        data_loaded.set("Vanha data edelleen käytössä.")
    if game_data is None:
        data_loaded.set("")

def start_loading_data():
    global thrower_data
    if file_path.get() in ['None', '']:
        data_loaded.set("Tiedosta ei valittu.")
        return
    print(file_path.get())
    return_values = load_data(file_path.get())
    if isinstance(return_values, bool) and return_values is False:
        data_loaded.set("Datan lataus epäonnistui")
        return None

    throw_array, team_names, start_team = return_values
    thrower_data = throw_array
    all_teams[0].set(team_names[0])
    all_teams[1].set(team_names[1])
    starting_team.set(start_team)

    # Insert data to entires in main window.
    for period in range(0, 2):
        for team in range(0, 2):
            for player in range(0, 4):
                t = int(not team)
                entires[period][t][player].set(throw_array[period][team][player][0])

    data_loaded.set("Data Ladattu")
    print(throw_array)

def launch_program():
    if not names.get() and not points_var.get():
        start_label.set("Ei mitään valittu")
    else:
        start_label.set("")
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
            fusion_app=app,
        )
        if val is True:
            start_label.set("Ohjelma ajoi onnistuneesti.")
        else:
            start_label.set("Ohjelmassa men jotain vikaan.")


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

    for col in range(0, 13):
        if col == 3 or col == 10: 
            continue
        ttk.Label(other_window, text="------").grid(row=row_idx, column=col)
    row_idx += 1

    make_period_entries(2, row_idx)
    row_idx += 6

    for col in range(0, 13):
        if col == 3 or col == 10: 
            continue
        ttk.Label(other_window, text="------").grid(row=row_idx, column=col)
    row_idx += 1

    def empty_fun():
        for period in range(0, 2):
            for team in range(0, 2):
                for player in range(0, 4):
                    for throw in range(0, 4):
                        player_points[period][team][player][throw].set("")

    def load_from_matrix():
        for period in range(0, 2):
            for team in range(0, 2):
                for player in range(0, 4):
                    for throw in range(1, 5):
                        player_points[period][team][player][throw-1].set(
                            thrower_data[period][team][player][throw]
                        )

    def save_to_matrix():
        for period in range(0, 2):
            for team in range(0, 2):
                for player in range(0, 4):
                    for throw in range(1, 5):
                        thrower_data[period][team][player][throw] = (
                            player_points[period][team][player][throw-1].get()
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
            entires[round_no-1][i-1].append(entry_var)


ttk.Button(setup_window, text="Etsi tiedosto", command=start_finding_file).grid(row=running_row, column=0)
file_path = tk.StringVar(setup_window, "None")
ttk.Label(setup_window, textvariable=file_path).grid(row=running_row, column=1)
running_row += 1

ttk.Button(setup_window, text="Lataa data", command=start_loading_data).grid(row=running_row, column=0)
data_loaded = tk.StringVar(setup_window)
ttk.Label(setup_window, textvariable=data_loaded).grid(row=running_row, column=1)
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

entires = [
    [[], []], # 1st period
    [[], []], # 2nd period
]

# Add the 1. period entires
make_entries(running_row, 1)
running_row += 4 + 1   # Add the entires and proceed to next empty row 

tk.Label(setup_window, text="1. Erän aloittaja").grid(row=running_row, column=0)
starting_team = tk.BooleanVar(setup_window, value=True)
ttk.Radiobutton(
    setup_window, 
    text="",
    variable=starting_team,
    value=True, 
).grid(row=running_row, column=1)
ttk.Radiobutton(
    setup_window, 
    text="",
    variable=starting_team,
    value=False, 
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

ttk.Button(setup_window, text="Pisteet", command=launch_points_window).grid(
    row=running_row,
    column=0,
)
running_row += 1

ttk.Button(setup_window, text="Aloita ohjelma", command=launch_program).grid(
    row=running_row,
    column=0,
)
running_row += 1

status = tk.StringVar(setup_window)
tk.Label(setup_window, textvariable=status, fg='#0000FF').grid(
    row=running_row,
    column=0,
)
running_row += 1

ttk.Button(setup_window, text="Poistu", command=lambda:setup_window.destroy()).grid(
    row=running_row,
    column=0
)
running_row += 1

start_label = tk.StringVar(setup_window)
ttk.Label(setup_window, textvariable=start_label).grid(row=running_row, column=0)
running_row += 1

setup_window.mainloop()