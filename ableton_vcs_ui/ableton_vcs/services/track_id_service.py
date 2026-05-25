class TrackIdService:
    def format_counter(self, number):
        return str(number).zfill(4)

    def get_previous_tracks_by_ableton_id(self, previous_track_map):
        previous_tracks = {}

        for global_track_id, track_data in previous_track_map.items():
            ableton_local_id = track_data.get("ableton_local_id")

            if ableton_local_id:
                previous_tracks[str(ableton_local_id)] = {
                    "global_track_id": global_track_id,
                    "track_data": track_data,
                }

        return previous_tracks

    def build_track_map_for_commit(
        self,
        current_tracks,
        previous_track_map,
        global_track_id_counter,
    ):
        previous_tracks_by_ableton_id = self.get_previous_tracks_by_ableton_id(
            previous_track_map
        )

        new_track_map = {}
        updated_counter = global_track_id_counter

        for track in current_tracks:
            ableton_local_id = str(track["ableton_local_id"])
            previous_match = previous_tracks_by_ableton_id.get(ableton_local_id)

            if previous_match:
                global_track_id = previous_match["global_track_id"]
                previous_track_data = previous_match["track_data"]

                new_track_map[global_track_id] = {
                    "ableton_local_id": ableton_local_id,
                    "track_type": track["track_type"],
                    "track_name": track["track_name"],
                    "current_version": previous_track_data.get("current_version", "0001"),
                    "status": "unchanged",
                }

            else:
                updated_counter += 1
                global_track_id = self.format_counter(updated_counter)

                new_track_map[global_track_id] = {
                    "ableton_local_id": ableton_local_id,
                    "track_type": track["track_type"],
                    "track_name": track["track_name"],
                    "current_version": "0001",
                    "status": "new",
                }

        return {
            "global_track_id_counter": updated_counter,
            "track_map": new_track_map,
        }