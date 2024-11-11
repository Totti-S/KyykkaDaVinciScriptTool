import numpy as np
from utils import find_file, load_data

def run_automatic_editor(
    start_offset: int = 1, # How many clips are at the start periods
    middle_offset: int = 1, # How many clips are at the between periods
    starting_team: bool = True, # Which team start the game first Home: True , Away: False
    home_team: str = 'Team1',
    away_team: str = 'Team2',
    dublicate_timeline: bool = True,
    add_names_to_clip: bool = True,
    add_score_to_clip: bool = True,
    thrower_data: np.ndarray[np.str_] | None = None,
    fusion_app = None
) -> bool:
    if fusion_app is None:
        global app
    else:
        app = fusion_app
    if not add_names_to_clip and not add_score_to_clip:
        print("Mitään ei ollut valittu lisättäväksi. Ohjelma loppuu...")
        return False

    if thrower_data is None:
        file_path = find_file()
        thrower_data, (home_team, away_team), starting_team = load_data(file_path)

    # Other config values
    textbox_name = 'Text1'
    score_board_bg_name = 'BackgroundRectangle'
    end_name_fade = True    # If the 'score' clip needs fade  
    fade_frames = 20    # How many frames will take to fade out something

    resolve = app.GetResolve()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    timeline = project.GetCurrentTimeline()

    # Set timeline to zero to not make keyframes in random place when using 'BezierSpline' or 'Polypath'
    timeline.SetCurrentTimecode(timeline.GetStartTimecode())
    resolve.OpenPage('edit')

    print('****************')
    # Duplicate the orginal timeline not to ruin 'the master tape'
    if dublicate_timeline:
        timeline = timeline.DuplicateTimeline("Edited Timeline")
    
    # Find cutted videotrack's
    # The first number is the baseline number. 
    # To get running frames remove the first number from start times
    videoclips = timeline.GetItemListInTrack('video', 1)
    baseline = videoclips[0].GetStart()
    clip_start_times = [clip.GetStart() - baseline for clip in videoclips]

    # Create Combound clip that then implements the right fusion composition
    combine_clip = timeline.CreateCompoundClip(videoclips)

    if add_names_to_clip and add_score_to_clip:
        comp = combine_clip.ImportFusionComp("E:\kyykkavids\Leikkaus välineet\Scoreboard_and_name_to_compound_clip.comp")
    elif not add_names_to_clip and add_score_to_clip:
        comp = combine_clip.ImportFusionComp("E:\kyykkavids\Leikkaus välineet\Scoreboard_to_compound_clip.comp")
    elif add_names_to_clip and not add_score_to_clip:
        comp = combine_clip.ImportFusionComp("E:\kyykkavids\Leikkaus välineet\\Name_to_compound_clip.comp")

    # Find the background to change the background between the periods
    if add_score_to_clip:
        scoreboard_background = comp.FindTool(score_board_bg_name)
        # Disable 2nd period numbers
        period_2_node_names = ['Team1P2Score', 'Team2P2Score', 'Team1TotalScore', 'Team2TotalScore']
        period_2_nodes = [comp.FindTool(name) for name in period_2_node_names]
        for node in period_2_nodes:
            node.Opacity1 = comp.BezierSpline()
            node.Opacity1[0] = 0

        for node in period_2_nodes[0:2]:
            node.StyledText = comp.BezierSpline()
            node.StyledText[0] = 80

        # Background of the period changes 0.12 between periods, add keyframes
        # NOTE I am not sure that you need this dublicate code before 'BezierSpline'
        scoreboard_background.Width[0] = 0.18
        scoreboard_background.Center[0] = {1: 0.105, 2: 0.9, 3: 0.0}
        scoreboard_background.Width = comp.BezierSpline()
        scoreboard_background.Center = comp.PolyPath()

        # 1st Period scoreboard configs
        scoreboard_background.Width[0] = 0.18
        scoreboard_background.Center[0] = {1: 0.105, 2: 0.9, 3: 0.0}
        period_1_node_names = ['Team1P1Score', 'Team2P1Score']
        period_1_nodes = [comp.FindTool(name) for name in period_1_node_names]
        for node in period_1_nodes:
            node.StyledText = comp.BezierSpline()
            node.StyledText[0] = 80
        # Set the team names to scoreboard
        team_name1_node = comp.FindTool('TeamName1')
        team_name1_node.StyledText = home_team
        team_name2_node = comp.FindTool('TeamName2')
        team_name2_node.StyledText = away_team

    if add_names_to_clip:
        name_node = comp.FindTool(textbox_name)
        # BezierSpline is needed to add keyframes and make the text change
        # Alternative way is to cut component to equal sizes with the clips
        name_node.StyledText = comp.BezierSpline()
        name_node.Opacity1 = comp.BezierSpline()
        name_node.Opacity1 = 1


    def add_names(period: int, start_frames: list[int], offset: int, starter_team: int) -> int:
        """Adds thrower name and throw scores to clips\n
        
        Parameters
        -----------
        period: Period number (1 or 2)\n
        start_frames: List of clips starting frames. These include possible offsetted clips \
            at the start of the period. Can include more than only periods frames\n
        offset: Number of clips that in the beginning of the period will be ignored.\n
        starter_team: Team to start. Either 0 or 1.\n

        Returns
        ----------
        last clip number that function counted
        """
        assert period in [1,2], (
            f"'Period'- field takes an input either '1' or '2'. Function got: '{period}'"
        )
        period -= 1
        clip_number = 0 + offset
        team = int(not starter_team) # First conversion removes condition from 1st 'if'
        for i in range(16):
            if i % 2 == 0:
                team = int(not team)
            if i < 8:
                player = i % 2 + 2 * (i // 4)
                name, st, nd, *_ = thrower_data[period][team][player]
            else:
                player = i % 2 + 2 * ((i - 8) // 4)
                name, _, _, st, nd = thrower_data[period][team][player]
            for score in [st, nd]:
                if score == "e":
                    break
                frame = start_frames[clip_number]
                name_node.StyledText[frame] = name
                clip_number += 1

        return clip_number

    def add_scores(
        period: int,
        start_frames: list[int],
        offset: int,
        team_nodes: list,
        starter_team: int,
    ) -> int:
        assert period in [1,2], (
            f"'Period'- field takes an input either '1' or '2'. Function got: '{period}'"
        )
        period -= 1
        clip_number = 0 + offset
        team = int(not starter_team) # First conversion removes condition from 1st 'if'
        scores = [80, 80]
        throws = [16, 16]
        for i in range(16):
            if i % 2 == 0:
                team = int(not team)
            if i < 8:
                player = i % 2 + 2 * (i // 4)
                _, st, nd, *_ = thrower_data[period][team][player]
            else:
                player = i % 2 + 2 * ((i - 8) // 4)
                *_, st, nd = thrower_data[period][team][player]
            for score in [st, nd]:
                if score == "e":
                    break
                elif st != 'h':
                    scores[team] -= int(score)
                frame = start_frames[clip_number+1] # Change the score after the clip
                throws[team] -= 1
                if scores[team] > 0:
                    team_nodes[team].StyledText[frame] = scores[team]
                else:
                    team_nodes[team].StyledText[frame] = throws[team]
                clip_number += 1
        return clip_number

    running_clip_number = 0

    # 1. period
    if add_names_to_clip:
        if start_offset:
            name_node.StyledText[0] = ""
        clips_processed = add_names(1, clip_start_times, start_offset, starting_team)

    if add_score_to_clip:
        clips_tmp = add_scores(1, clip_start_times, start_offset, period_1_nodes, starting_team)
        if add_names_to_clip:
            assert clips_processed == clips_tmp, (
                f"Clip processed was not same ! (name == {clips_processed}, score == {clips_tmp})"
            )
        clips_processed = clips_tmp
    running_clip_number += clips_processed

    # 2. period
    if add_names_to_clip and middle_offset:
        frame_number = clip_start_times[running_clip_number]
        # Fade out the name
        name_node.Opacity1[frame_number - 1 - fade_frames] = 1
        name_node.Opacity1[frame_number - 1] = 0
        name_node.Opacity1[frame_number] = 1
        name_node.StyledText[frame_number] = ""

    # Instant transistion to 2nd period scoreboard
    if add_score_to_clip:
        frame_number = clip_start_times[running_clip_number+middle_offset]
        scoreboard_background.Width[frame_number - 1] = 0.18
        scoreboard_background.Center[frame_number - 1] = {1: 0.105, 2: 0.9, 3: 0.0}
        scoreboard_background.Width[frame_number] = 0.3
        scoreboard_background.Center[frame_number] = {1: 0.165, 2: 0.9, 3: 0.0}
        for node in period_2_nodes:
            node.Opacity1[frame_number - 1] = 0
            node.Opacity1[frame_number] = 1

    nd_period_frames = clip_start_times[running_clip_number:]
   
    if add_names_to_clip:
        clips_processed = add_names(2, nd_period_frames, middle_offset, int(not starting_team))

    if add_score_to_clip:
        clips_tmp = add_scores(2, nd_period_frames, middle_offset, period_2_nodes[0:2], int(not starting_team))
        if add_names_to_clip:
            assert clips_processed == clips_tmp, (
                f"Clip processed was not same ! (name == {clips_processed}, score == {clips_tmp})"
            )
        clips_processed = clips_tmp
    running_clip_number += clips_processed

    if end_name_fade and add_names_to_clip:
        frame_number = clip_start_times[running_clip_number]
        name_node.Opacity1[frame_number - 1 - fade_frames] = 1
        name_node.Opacity1[frame_number - 1] = 0

    return True

if __name__ == "__main__":
    # out = run_automatic_editor()
    # print(f"Editointi loppui. Editointi palautti arvon: {out}")
    print(app)