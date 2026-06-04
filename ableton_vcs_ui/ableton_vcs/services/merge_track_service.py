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
                rows.append(
                    self.compare_existing_track(
                        global_track_id,
                        left_track,
                        right_track
                    )
                )

            elif left_track and not right_track:
                rows.append(
                    self.build_only_left_row(
                        global_track_id,
                        left_track
                    )
                )

            elif right_track and not left_track:
                rows.append(
                    self.build_only_right_row(
                        global_track_id,
                        right_track
                    )
                )

        return rows

    def compare_existing_track(self, global_track_id, left_track, right_track):
        left_version = self.get_track_version(left_track)
        right_version = self.get_track_version(right_track)

        if left_version == right_version:
            merge_status = "same"
            label = "Same"
        else:
            merge_status = "different_version"
            label = "Changed"

        parent_group_global_id = (
            left_track.get("parent_group_global_id")
            or right_track.get("parent_group_global_id")
        )

        return {
            "global_track_id": global_track_id,
            "track_name": left_track.get("track_name") or right_track.get("track_name", "Untitled"),
            "track_type": left_track.get("track_type") or right_track.get("track_type", "Unknown"),
            "parent_group_global_id": parent_group_global_id,
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
            "parent_group_global_id": left_track.get("parent_group_global_id"),
            "merge_status": "only_left",
            "label": "Only left",
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
            "parent_group_global_id": right_track.get("parent_group_global_id"),
            "merge_status": "only_right",
            "label": "Only right",
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
            "current_version": self.get_track_version(track),
            "status": track.get("status", ""),
            "changed_reasons": track.get("changed_reasons", []),
            "parent_group_global_id": track.get("parent_group_global_id"),
            "child_track_global_ids": track.get("child_track_global_ids", []),
            "content_fingerprint": track.get("content_fingerprint", ""),
            "membership_fingerprint": track.get("membership_fingerprint", ""),
        }

    def get_track_version(self, track):
        return (
            track.get("current_version")
            or track.get("track_version")
            or "0001"
        )