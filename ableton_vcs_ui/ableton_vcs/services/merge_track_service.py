class MergeTrackService:
    def compare_track_maps(self, left_commit, right_commit):
        left_track_map = left_commit.get("track_map", {})
        right_track_map = right_commit.get("track_map", {})

        all_track_ids = sorted(
            set(left_track_map.keys()) | set(right_track_map.keys())
        )

        rows = []

        for global_track_id in all_track_ids:
            left_track = left_track_map.get(global_track_id)
            right_track = right_track_map.get(global_track_id)

            if left_track and right_track:
                row = self.compare_existing_track(
                    global_track_id,
                    left_track,
                    right_track
                )
                rows.append(row)

            elif left_track and not right_track:
                row = self.build_only_left_row(
                    global_track_id,
                    left_track
                )
                rows.append(row)

            elif right_track and not left_track:
                row = self.build_only_right_row(
                    global_track_id,
                    right_track
                )
                rows.append(row)

        return rows

    def compare_existing_track(self, global_track_id, left_track, right_track):
        left_version = left_track.get("current_version", "0001")
        right_version = right_track.get("current_version", "0001")

        if left_version == right_version:
            merge_status = "same"
            label = "Same"
        else:
            merge_status = "different_version"
            label = "Different version"

        return {
            "global_track_id": global_track_id,
            "track_name": left_track.get("track_name") or right_track.get("track_name", "Untitled"),
            "track_type": left_track.get("track_type") or right_track.get("track_type", "Unknown"),
            "merge_status": merge_status,
            "label": label,
            "left": self.build_existing_side(left_track),
            "right": self.build_existing_side(right_track),
        }

    def build_only_left_row(self, global_track_id, left_track):
        return {
            "global_track_id": global_track_id,
            "track_name": left_track.get("track_name", "Untitled"),
            "track_type": left_track.get("track_type", "Unknown"),
            "merge_status": "only_left",
            "label": "Missing from right",
            "left": self.build_existing_side(left_track),
            "right": {
                "exists": False,
            },
        }

    def build_only_right_row(self, global_track_id, right_track):
        return {
            "global_track_id": global_track_id,
            "track_name": right_track.get("track_name", "Untitled"),
            "track_type": right_track.get("track_type", "Unknown"),
            "merge_status": "only_right",
            "label": "New in right",
            "left": {
                "exists": False,
            },
            "right": self.build_existing_side(right_track),
        }

    def build_existing_side(self, track):
        return {
            "exists": True,
            "track_name": track.get("track_name", "Untitled"),
            "track_type": track.get("track_type", "Unknown"),
            "current_version": track.get("current_version", "0001"),
            "status": track.get("status", ""),
            "ableton_local_id": track.get("ableton_local_id", ""),
        }