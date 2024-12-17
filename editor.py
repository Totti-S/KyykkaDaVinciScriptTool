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
    points_direction: bool = True,
    clips_missing_per_period: list[list[int]] = [[], []],
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
    textbox_name = 'NameText'
    scoreboard_merge_name = 'ScoreBoardMerge'
    scoreboard_team_turn_names = ['TurnTeam1', 'TurnTeam2']
    direction_node_name = 'Direction'
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
        comp = combine_clip.ImportFusionComp("E:\kyykkavids\Leikkaus välineet\Scoreboard_and_name.comp")
    elif not add_names_to_clip and add_score_to_clip:
        comp = combine_clip.ImportFusionComp("E:\kyykkavids\Leikkaus välineet\Scoreboard.comp")
    elif add_names_to_clip and not add_score_to_clip:
        comp = combine_clip.ImportFusionComp("E:\kyykkavids\Leikkaus välineet\PlayerName.comp")

    # Find the background to change the background between the periods
    if add_score_to_clip:
        scoreboard_background = comp.FindTool(scoreboard_merge_name)
        scoreboard_background.Blend = comp.BezierSpline()
        scoreboard_background.Blend[0] = 1

        # Initialize turn indicators
        turn_nodes = [comp.FindTool(name) for name in scoreboard_team_turn_names]
        for node in turn_nodes:
            node.Blend = comp.BezierSpline()
            node.Blend[0] = 0
        
        direction_node = comp.FindTool(direction_node_name)
        print(direction_node)
        if direction_node is not None:
            direction_node.StyledText = -1 if points_direction else 1

        # Initialize 1. period
        period_1_node_names = ['Team1P1Score', 'Team2P1Score']
        period_1_nodes = [comp.FindTool(name) for name in period_1_node_names]
        for node in period_1_nodes:
            node.StyledText = comp.BezierSpline()
            node.StyledText[0] = 80

        # Initialize 2. period
        period_2_node_names = ['Team1P2Score', 'Team2P2Score']
        period_2_nodes = [comp.FindTool(name) for name in period_2_node_names]
        for node in period_2_nodes:
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


    def add_names(
        period: int,
        start_frames: list[int],
        offset: int,
        starter_team: int,
        clips_missing: list[int]
    ) -> int:
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
            if i in clips_missing:
                continue
            if i < 8:
                player = i % 2 + 2 * (i // 4)
                name, st, nd, *_ = thrower_data[period][team][player]
            else:
                player = i % 2 + 2 * ((i - 8) // 4)
                name, _, _, st, nd = thrower_data[period][team][player]
            for j, score in enumerate([st, nd], 1):
                if score == "e":
                    break
                frame = start_frames[clip_number]
                name_node.StyledText[frame] = name
                if (i * 2 + j) not in clips_missing:
                    clip_number += 1

        return clip_number

    def add_scores(
        period: int,
        start_frames: list[int],
        offset: int,
        team_nodes: list,
        starter_team: int,
        clips_missing: list[int],
    ) -> int:
        assert period in [1,2], (
            f"'Period'- field takes an input either '1' or '2'. Function got: '{period}'"
        )
        period -= 1
        clip_number = 0 + offset
        team = starter_team
        scores = [80, 80]
        throws = [16, 16]
        direction = -1 if points_direction else 1
        frame = start_frames[clip_number]
        # Turn nodes
        turn_nodes[team].Blend[frame] = 1
        for i in range(16):
            if i % 2 == 0 and i != 0:
                # If team changes, so does the turn indicator
                turn_nodes[team].Blend[frame - 1] = 1
                turn_nodes[team].Blend[frame] = 0
                team = int(not team)
                turn_nodes[team].Blend[frame - 1] = 0
                turn_nodes[team].Blend[frame] = 1
            if i < 8:
                player = i % 2 + 2 * (i // 4)
                _, st, nd, *_ = thrower_data[period][team][player]
            else:
                player = i % 2 + 2 * ((i - 8) // 4)
                *_, st, nd = thrower_data[period][team][player]
            for j, score in enumerate([st, nd], 1):
                if score == "e":
                    break
                elif score != 'h':
                    scores[team] -= int(score)
                frame = start_frames[clip_number+1] # Change the score after the clip
                throws[team] -= 1
                if scores[team] > 0:
                    team_nodes[team].StyledText[frame] = scores[team] * direction
                else:
                    team_nodes[team].StyledText[frame] = throws[team] * direction * -1
                if (i * 2 + j) not in clips_missing:
                    clip_number += 1
        return clip_number

    running_clip_number = 0

    # 1. period
    if add_names_to_clip:
        if start_offset:
            name_node.StyledText[0] = ""
        clips_processed = add_names(1, clip_start_times, start_offset, int(starting_team), clips_missing_per_period[0])

    if add_score_to_clip:
        # The start values need to ne adjusted
        frame = clip_start_times[0]
        direction = -1 if points_direction else 1
        for node in [*period_1_nodes, *period_2_nodes]:
            node.StyledText[frame] = 80 * direction
        
        if start_offset:
            frame = clip_start_times[start_offset]
            scoreboard_background.Blend[0] = 0
            scoreboard_background.Blend[frame - 1] = 0
            scoreboard_background.Blend[frame] = 1
        
        clips_tmp = add_scores(1, clip_start_times, start_offset, period_1_nodes, int(starting_team), clips_missing_per_period[0])
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

    nd_period_frames = clip_start_times[running_clip_number:]
   
    if add_names_to_clip:
        clips_processed = add_names(2, nd_period_frames, middle_offset, int(not starting_team), clips_missing_per_period[1])

    if add_score_to_clip:
        clips_tmp = add_scores(2, nd_period_frames, middle_offset, period_2_nodes[0:2], int(not starting_team), clips_missing_per_period[1])
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

    if len(clip_start_times) > running_clip_number + 1:
        frame = clip_start_times[running_clip_number + 1]
        scoreboard_background.Blend[frame - 1] = 1
        scoreboard_background.Blend[frame] = 0

    return True

if __name__ == "__main__":
    out = run_automatic_editor(points_direction=False, middle_offset=0)
    print(f"Editointi loppui. Editointi palautti arvon: {out}")
    # print(app)