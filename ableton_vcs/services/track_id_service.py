import hashlib
import json


class TrackIdService:
    def format_counter(self, number):
        return str(number).zfill(4)

    def parse_version(self, value):
        if value is None:
            return 1

        try:
            return int(str(value))
        except ValueError:
            return 1

    def format_version(self, number):
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

    def get_max_track_version(self, metadata, global_track_id):
        max_version = 0

        for commit in metadata.get("commits", []):
            for track_id, track_data in commit.get("track_map", {}).items():
                if str(track_id) != str(global_track_id):
                    continue

                version_value = (
                    track_data.get("current_version")
                    or track_data.get("track_version")
                    or "0001"
                )

                max_version = max(
                    max_version,
                    self.parse_version(version_value)
                )

        return max_version

    def build_membership_fingerprint(self, child_global_ids):
        serialized = json.dumps(
            [str(child_id) for child_id in child_global_ids],
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def build_track_map_for_commit(
        self,
        current_tracks,
        previous_track_map,
        global_track_id_counter,
        metadata=None,
    ):
        if metadata is None:
            metadata = {"commits": []}

        previous_tracks_by_ableton_id = self.get_previous_tracks_by_ableton_id(
            previous_track_map
        )

        new_track_map = {}
        updated_counter = global_track_id_counter
        local_to_global_id = {}

        for track in current_tracks:
            ableton_local_id = str(track["ableton_local_id"])
            previous_match = previous_tracks_by_ableton_id.get(ableton_local_id)

            if previous_match:
                global_track_id = previous_match["global_track_id"]
                previous_track_data = previous_match["track_data"]
                is_new = False

            else:
                updated_counter += 1
                global_track_id = self.format_counter(updated_counter)
                previous_track_data = None
                is_new = True

            new_track_map[global_track_id] = {
                "ableton_local_id": ableton_local_id,
                "track_type": track["track_type"],
                "track_name": track["track_name"],
                "track_color": track.get("track_color", ""),
                "content_fingerprint": track.get("content_fingerprint", ""),
                "membership_fingerprint": "",
                "child_track_global_ids": [],
                "current_version": "0001",
                "status": "new" if is_new else "unchanged",
                "changed_reasons": [],
                "parent_group_global_id": None,
                "_previous_track_data": previous_track_data,
                "_is_new": is_new,
            }

            local_to_global_id[ableton_local_id] = global_track_id

        self.apply_parent_group_ids(
            current_tracks=current_tracks,
            new_track_map=new_track_map,
            local_to_global_id=local_to_global_id,
        )

        self.apply_group_membership(
            current_tracks=current_tracks,
            new_track_map=new_track_map,
            local_to_global_id=local_to_global_id,
        )

        self.apply_versions_and_statuses(
            new_track_map=new_track_map,
            metadata=metadata,
        )

        for track_data in new_track_map.values():
            track_data.pop("_previous_track_data", None)
            track_data.pop("_is_new", None)

        return {
            "global_track_id_counter": updated_counter,
            "track_map": new_track_map,
        }

    def apply_parent_group_ids(self, current_tracks, new_track_map, local_to_global_id):
        for track in current_tracks:
            ableton_local_id = str(track["ableton_local_id"])
            global_track_id = local_to_global_id.get(ableton_local_id)

            if not global_track_id:
                continue

            parent_group_local_id = track.get("parent_group_local_id")

            if parent_group_local_id is None:
                new_track_map[global_track_id]["parent_group_global_id"] = None
                continue

            parent_group_local_id = str(parent_group_local_id)
            parent_group_global_id = local_to_global_id.get(parent_group_local_id)

            new_track_map[global_track_id]["parent_group_global_id"] = parent_group_global_id

    def apply_group_membership(self, current_tracks, new_track_map, local_to_global_id):
        children_by_group = {}

        for track in current_tracks:
            ableton_local_id = str(track["ableton_local_id"])
            global_track_id = local_to_global_id.get(ableton_local_id)

            if not global_track_id:
                continue

            parent_group_global_id = new_track_map[global_track_id].get("parent_group_global_id")

            if not parent_group_global_id:
                continue

            children_by_group.setdefault(parent_group_global_id, [])
            children_by_group[parent_group_global_id].append(global_track_id)

        for global_track_id, track_data in new_track_map.items():
            if track_data.get("track_type") != "GroupTrack":
                continue

            child_global_ids = children_by_group.get(global_track_id, [])

            track_data["child_track_global_ids"] = child_global_ids
            track_data["membership_fingerprint"] = self.build_membership_fingerprint(
                child_global_ids
            )

    def apply_versions_and_statuses(self, new_track_map, metadata):
        for global_track_id, track_data in new_track_map.items():
            previous_track_data = track_data.get("_previous_track_data")
            is_new = track_data.get("_is_new", False)

            if is_new or previous_track_data is None:
                track_data["current_version"] = "0001"
                track_data["status"] = "new"
                track_data["changed_reasons"] = ["new_track"]
                continue

            changed_reasons = self.get_changed_reasons(
                current_track=track_data,
                previous_track=previous_track_data,
            )

            if not changed_reasons:
                track_data["current_version"] = (
                    previous_track_data.get("current_version")
                    or previous_track_data.get("track_version")
                    or "0001"
                )
                track_data["status"] = "unchanged"
                track_data["changed_reasons"] = []
                continue

            max_existing_version = self.get_max_track_version(
                metadata=metadata,
                global_track_id=global_track_id,
            )

            track_data["current_version"] = self.format_version(max_existing_version + 1)
            track_data["status"] = "modified"
            track_data["changed_reasons"] = changed_reasons

    def get_changed_reasons(self, current_track, previous_track):
        reasons = []

        previous_content_fingerprint = previous_track.get("content_fingerprint", "")
        current_content_fingerprint = current_track.get("content_fingerprint", "")

        if previous_content_fingerprint:
            if current_content_fingerprint != previous_content_fingerprint:
                reasons.append("content_changed")

        previous_parent_group_id = previous_track.get("parent_group_global_id")
        current_parent_group_id = current_track.get("parent_group_global_id")

        if previous_parent_group_id != current_parent_group_id:
            reasons.append("group_location_changed")

        if current_track.get("track_type") == "GroupTrack":
            previous_membership_fingerprint = previous_track.get("membership_fingerprint", "")
            current_membership_fingerprint = current_track.get("membership_fingerprint", "")

            if previous_membership_fingerprint:
                if current_membership_fingerprint != previous_membership_fingerprint:
                    reasons.append("group_membership_changed")

        return reasons