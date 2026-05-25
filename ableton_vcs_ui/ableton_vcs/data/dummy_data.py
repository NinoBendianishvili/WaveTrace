DUMMY_COMMITS = {
    "branch_label": "MAIN",
    "selected_commit": "c6",
    "commits": [
        {"hash": "c1", "name": "Initial project", "date": "2026-04-12 18:40", "comment": "Created the project structure and imported the first demo stems.", "audio_path": "audio/initial_project.wav", "predecessors": [], "successors": ["c2"], "lane": 0, "y": 690},
        {"hash": "c2", "name": "Instrumental mix", "date": "2026-04-14 14:20", "comment": "Balanced the instrumental layers and set initial levels for drums, bass, and synths.", "audio_path": "audio/instrumental_mix.wav", "predecessors": ["c1"], "successors": ["c3"], "lane": 0, "y": 570},
        {"hash": "c3", "name": "Main vocals added", "date": "2026-04-16 20:05", "comment": "Recorded and aligned the main vocal takes, then added light cleanup processing.", "audio_path": "audio/main_vocals_added.wav", "predecessors": ["c2"], "successors": ["c4"], "lane": 0, "y": 440},
        {"hash": "c4", "name": "Harmonies added", "date": "2026-04-18 13:10", "comment": "Added backvocals and harmonies to the chorus of the track with reverb but not much effects.", "audio_path": "audio/harmonies_added.wav", "predecessors": ["c3"], "successors": ["c5", "b1"], "lane": 0, "y": 290},
        {"hash": "c5", "name": "Balanced mix", "date": "2026-04-20 10:45", "comment": "Refined the balance between vocals and instruments and adjusted the stereo image.", "audio_path": "audio/balanced_mix.wav", "predecessors": ["c4"], "successors": ["c6"], "lane": 0, "y": 190},
        {"hash": "c6", "name": "Mix with vocals", "date": "2026-04-22 14:32", "comment": "Finalized the main version with lead vocals, backing vocals, and restrained reverb.", "audio_path": "audio/mix_with_vocals.wav", "predecessors": ["c5"], "successors": [], "lane": 0, "y": 90},
        {"hash": "b1", "name": "Vocal effects", "date": "2026-04-18 19:00", "comment": "Created a side branch to try delay throws and a more spacious effects chain.", "audio_path": "audio/vocal_effects.wav", "predecessors": ["c4"], "successors": ["b2"], "lane": 1, "y": 360},
        {"hash": "b2", "name": "Reverb experiments", "date": "2026-04-16 23:20", "comment": "Tested heavier reverb tails and ambient transitions for the vocal branch.", "audio_path": "audio/reverb_experiments.wav", "predecessors": ["b1"], "successors": [], "lane": 1, "y": 445}
    ]
}




def build_demo_merge_groups():
    return [
        {"group": "Drums", "tracks": [{"name": "Kick In", "status": "unchanged"}, {"name": "Kick Out", "status": "unchanged"}, {"name": "Snare Top", "status": "collision"}, {"name": "Snare Bottom", "status": "unchanged"}, {"name": "HiHat", "status": "new"}, {"name": "Drum Room", "status": "collision"}]},
        {"group": "Perc", "tracks": [{"name": "Shaker", "status": "new"}, {"name": "Tamb", "status": "unchanged"}, {"name": "Clap Layer", "status": "collision"}, {"name": "Snap FX", "status": "new"}, {"name": "Loop A", "status": "unchanged"}]},
        {"group": "Bass", "tracks": [{"name": "Bass DI", "status": "collision"}, {"name": "Bass Amp", "status": "unchanged"}, {"name": "Sub Bass", "status": "new"}, {"name": "Bass FX", "status": "collision"}, {"name": "Bass Print", "status": "unchanged"}]},
        {"group": "Synths", "tracks": [{"name": "Pad Main", "status": "unchanged"}, {"name": "Pad Wide", "status": "new"}, {"name": "Lead Mono", "status": "collision"}, {"name": "Lead Stack", "status": "new"}, {"name": "Arp High", "status": "unchanged"}, {"name": "Arp Low", "status": "collision"}]},
        {"group": "Gtrs", "tracks": [{"name": "Gtr L", "status": "unchanged"}, {"name": "Gtr R", "status": "unchanged"}, {"name": "Gtr Clean", "status": "new"}, {"name": "Gtr Dirty", "status": "collision"}, {"name": "Gtr FX", "status": "new"}]},
        {"group": "Keys", "tracks": [{"name": "Piano Main", "status": "unchanged"}, {"name": "Piano Soft", "status": "new"}, {"name": "E-Piano", "status": "collision"}, {"name": "Bell Layer", "status": "new"}, {"name": "Organ Bed", "status": "unchanged"}]},
        {"group": "Vocals", "tracks": [{"name": "Lead Vox", "status": "collision"}, {"name": "Lead Double", "status": "new"}, {"name": "Backvox L", "status": "collision"}, {"name": "Backvox R", "status": "collision"}, {"name": "Harmony High", "status": "new"}, {"name": "Harmony Low", "status": "unchanged"}]},
        {"group": "FX", "tracks": [{"name": "Impact 1", "status": "new"}, {"name": "Riser", "status": "new"}, {"name": "Downlifter", "status": "unchanged"}, {"name": "Reverse Vox", "status": "collision"}, {"name": "Noise Bed", "status": "unchanged"}]},
        {"group": "Buses", "tracks": [{"name": "Drum Bus", "status": "collision"}, {"name": "Music Bus", "status": "unchanged"}, {"name": "Vox Bus", "status": "collision"}, {"name": "FX Bus", "status": "new"}, {"name": "Mix Print", "status": "unchanged"}]},
    ]
