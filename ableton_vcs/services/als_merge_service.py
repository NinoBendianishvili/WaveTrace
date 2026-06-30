import copy
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


TRACK_TAGS = {
    "MidiTrack",
    "AudioTrack",
    "ReturnTrack",
    "GroupTrack",
}

GLOBAL_ID_TAGS_EXACT = {
    "Pointee",
    "AutomationTarget",
    "ModulationTarget",
}


class AlsMergeService:
    def local_name(self, tag):
        return tag.split("}")[-1]

    def is_als(self, path):
        return str(path).lower().endswith(".als")

    def load_xml(self, path):
        path = Path(path)

        if self.is_als(path):
            with gzip.open(path, "rb") as file:
                return ET.parse(file)

        return ET.parse(path)

    def save_xml(self, tree, path):
        path = Path(path)

        xml_bytes = ET.tostring(
            tree.getroot(),
            encoding="utf-8",
            xml_declaration=True,
        )

        if self.is_als(path):
            with gzip.open(path, "wb") as file:
                file.write(xml_bytes)
        else:
            with path.open("wb") as file:
                file.write(xml_bytes)

    def to_int(self, value):
        try:
            return int(value)
        except Exception:
            return None

    def is_global_internal_id_tag(self, tag):
        return (
            tag in GLOBAL_ID_TAGS_EXACT
            or tag.startswith("ControllerTargets.")
            or tag.endswith("ModulationTarget")
        )

    def find_tracks(self, root):
        tracks = []

        for element in root.iter():
            if self.local_name(element.tag) in TRACK_TAGS:
                tracks.append(element)

        return tracks

    def get_tracks_container(self, root):
        for element in root.iter():
            if self.local_name(element.tag) == "Tracks":
                return element

        raise ValueError("Could not find <Tracks> container.")

    def get_next_pointee_id(self, root):
        for element in root.iter():
            if self.local_name(element.tag) == "NextPointeeId":
                value = self.to_int(element.attrib.get("Value"))

                if value is not None:
                    return element, value

        raise ValueError("Could not find <NextPointeeId>.")

    def max_track_id(self, root):
        max_id = -1

        for element in root.iter():
            tag = self.local_name(element.tag)

            if tag in TRACK_TAGS and "Id" in element.attrib:
                value = self.to_int(element.attrib["Id"])

                if value is not None:
                    max_id = max(max_id, value)

        return max_id

    def find_parent(self, root, child_to_find):
        for parent in root.iter():
            for child in list(parent):
                if child is child_to_find:
                    return parent

        return None

    def find_track_by_ableton_id(self, root, ableton_track_id):
        ableton_track_id = str(ableton_track_id)

        for track in self.find_tracks(root):
            if str(track.attrib.get("Id")) == ableton_track_id:
                return track

        return None

    def remove_track_from_root(self, root, track):
        parent = self.find_parent(root, track)

        if parent is None:
            return False

        parent.remove(track)
        return True

    def collect_sends_blocks(self, track):
        sends_blocks = []

        for element in track.iter():
            if self.local_name(element.tag) == "Sends":
                sends_blocks.append(element)

        return sends_blocks

    def find_destination_send_template_track(self, copied_track, destination_root):
        copied_type = self.local_name(copied_track.tag)

        for track in self.find_tracks(destination_root):
            if self.local_name(track.tag) == copied_type:
                return track

        for track in self.find_tracks(destination_root):
            if self.local_name(track.tag) in {"AudioTrack", "MidiTrack"}:
                return track

        return None

    def clone_sends_from_destination(self, copied_track, destination_root):
        template_track = self.find_destination_send_template_track(
            copied_track,
            destination_root,
        )

        if template_track is None:
            return

        copied_sends = self.collect_sends_blocks(copied_track)
        template_sends = self.collect_sends_blocks(template_track)

        if not copied_sends or not template_sends:
            return

        for index, old_sends in enumerate(copied_sends):
            if index < len(template_sends):
                new_sends = copy.deepcopy(template_sends[index])
            else:
                new_sends = copy.deepcopy(template_sends[-1])

            parent = self.find_parent(copied_track, old_sends)

            if parent is None:
                continue

            old_index = list(parent).index(old_sends)
            parent.remove(old_sends)
            parent.insert(old_index, new_sends)

    def remap_global_internal_ids_unique_per_element(self, track, next_id_start):
        next_id = next_id_start

        for element in track.iter():
            tag = self.local_name(element.tag)

            if self.is_global_internal_id_tag(tag) and "Id" in element.attrib:
                element.attrib["Id"] = str(next_id)
                next_id += 1

        return next_id

    def build_source_ableton_id_to_global_id(self, track_map):
        result = {}

        for global_track_id, track_data in track_map.items():
            ableton_local_id = track_data.get("ableton_local_id")

            if ableton_local_id:
                result[str(ableton_local_id)] = str(global_track_id)

        return result

    def build_global_id_to_ableton_id(self, track_map):
        result = {}

        for global_track_id, track_data in track_map.items():
            ableton_local_id = track_data.get("ableton_local_id")

            if ableton_local_id:
                result[str(global_track_id)] = str(ableton_local_id)

        return result

    def remap_track_group_references(
        self,
        copied_track,
        source_old_track_id_to_new_track_id,
        source_ableton_id_to_global_id,
        base_global_id_to_ableton_id,
        selected_base_global_ids,
    ):
        selected_base_global_ids = set(str(item) for item in selected_base_global_ids)

        for element in copied_track.iter():
            tag = self.local_name(element.tag)

            if tag not in {"TrackGroupId", "LinkedTrackGroupId"}:
                continue

            old_group_ableton_id = element.attrib.get("Value")

            if old_group_ableton_id is None or old_group_ableton_id == "-1":
                continue

            old_group_ableton_id = str(old_group_ableton_id)

            if old_group_ableton_id in source_old_track_id_to_new_track_id:
                element.attrib["Value"] = source_old_track_id_to_new_track_id[old_group_ableton_id]
                continue

            parent_group_global_id = source_ableton_id_to_global_id.get(old_group_ableton_id)

            if (
                parent_group_global_id
                and parent_group_global_id in selected_base_global_ids
                and parent_group_global_id in base_global_id_to_ableton_id
            ):
                element.attrib["Value"] = base_global_id_to_ableton_id[parent_group_global_id]
                continue

            element.attrib["Value"] = "-1"

    def insert_track_in_correct_position(self, tracks_container, copied_track):
        copied_type = self.local_name(copied_track.tag)
        children = list(tracks_container)

        if copied_type in {"AudioTrack", "MidiTrack", "GroupTrack"}:
            for index, child in enumerate(children):
                if self.local_name(child.tag) == "ReturnTrack":
                    tracks_container.insert(index, copied_track)
                    return

            tracks_container.append(copied_track)
            return

        if copied_type == "ReturnTrack":
            last_return_index = None

            for index, child in enumerate(children):
                if self.local_name(child.tag) == "ReturnTrack":
                    last_return_index = index

            if last_return_index is not None:
                tracks_container.insert(last_return_index + 1, copied_track)
            else:
                tracks_container.append(copied_track)

            return

        tracks_container.append(copied_track)

    def get_track_version(self, track_data):
        return (
            track_data.get("current_version")
            or track_data.get("track_version")
            or "0001"
        )

    def build_children_by_parent(self, track_map):
        children_by_parent = {}

        for global_track_id, track_data in track_map.items():
            global_track_id = str(global_track_id)
            parent_id = track_data.get("parent_group_global_id")

            children_by_parent.setdefault(None, [])
            children_by_parent.setdefault(global_track_id, [])

            if parent_id:
                parent_id = str(parent_id)
                children_by_parent.setdefault(parent_id, [])
                children_by_parent[parent_id].append(global_track_id)

        return children_by_parent

    def get_descendant_ids(self, parent_id, children_by_parent):
        result = []

        def collect(current_parent_id):
            for child_id in children_by_parent.get(current_parent_id, []):
                result.append(child_id)
                collect(child_id)

        collect(str(parent_id))
        return result

    def expand_deleted_groups(self, base_track_map, selected_base_global_ids):
        selected = set(str(item) for item in selected_base_global_ids)
        children_by_parent = self.build_children_by_parent(base_track_map)

        deleted = set()

        for global_track_id, track_data in base_track_map.items():
            global_track_id = str(global_track_id)

            if global_track_id not in selected:
                deleted.add(global_track_id)

                if track_data.get("track_type") == "GroupTrack":
                    deleted.update(
                        self.get_descendant_ids(
                            global_track_id,
                            children_by_parent,
                        )
                    )

        return deleted

    def build_tracks_to_delete_from_base(self, base_track_map, selected_base_global_ids):
        deleted_global_ids = self.expand_deleted_groups(
            base_track_map,
            selected_base_global_ids,
        )

        delete_ableton_ids = []

        for global_track_id in deleted_global_ids:
            track_data = base_track_map.get(global_track_id)

            if not track_data:
                continue

            ableton_local_id = track_data.get("ableton_local_id")

            if ableton_local_id:
                delete_ableton_ids.append(str(ableton_local_id))

        return delete_ableton_ids

    def should_copy_added_track(
        self,
        global_track_id,
        base_track_map,
        added_track_map,
        selected_base_global_ids,
        selected_added_global_ids,
    ):
        global_track_id = str(global_track_id)
        selected_added_global_ids = set(str(item) for item in selected_added_global_ids)

        if global_track_id not in selected_added_global_ids:
            return False

        added_track = added_track_map.get(global_track_id)

        if added_track is None:
            return False

        base_track = base_track_map.get(global_track_id)

        if base_track is None:
            return True

        base_version = self.get_track_version(base_track)
        added_version = self.get_track_version(added_track)

        if base_version == added_version:
            return False

        return True

    def collect_required_parent_groups(self, selected_added_global_ids, added_track_map, base_track_map):
        selected = set(str(item) for item in selected_added_global_ids)

        changed = True

        while changed:
            changed = False

            for global_track_id in list(selected):
                track_data = added_track_map.get(global_track_id)

                if not track_data:
                    continue

                parent_group_global_id = track_data.get("parent_group_global_id")

                if not parent_group_global_id:
                    continue

                parent_group_global_id = str(parent_group_global_id)

                if parent_group_global_id not in selected:
                    selected.add(parent_group_global_id)
                    changed = True

        return selected

    def sort_tracks_parent_before_children(self, global_ids, track_map):
        selected = set(str(item) for item in global_ids)
        result = []
        visited = set()

        def visit(global_track_id):
            global_track_id = str(global_track_id)

            if global_track_id in visited:
                return

            track_data = track_map.get(global_track_id)

            if not track_data:
                return

            parent_group_id = track_data.get("parent_group_global_id")

            if parent_group_id and str(parent_group_id) in selected:
                visit(str(parent_group_id))

            visited.add(global_track_id)
            result.append(global_track_id)

        ordered_by_ableton = sorted(
            selected,
            key=lambda item: int(track_map[item].get("ableton_local_id", 0)),
        )

        for global_track_id in ordered_by_ableton:
            visit(global_track_id)

        return result

    def build_added_copy_plan(
        self,
        base_track_map,
        added_track_map,
        selected_base_global_ids,
        selected_added_global_ids,
    ):
        selected_added_global_ids = self.collect_required_parent_groups(
            selected_added_global_ids=selected_added_global_ids,
            added_track_map=added_track_map,
            base_track_map=base_track_map,
        )

        copy_global_ids = []

        for global_track_id in selected_added_global_ids:
            if self.should_copy_added_track(
                global_track_id=global_track_id,
                base_track_map=base_track_map,
                added_track_map=added_track_map,
                selected_base_global_ids=selected_base_global_ids,
                selected_added_global_ids=selected_added_global_ids,
            ):
                copy_global_ids.append(str(global_track_id))

        return self.sort_tracks_parent_before_children(
            copy_global_ids,
            added_track_map,
        )

    def validate_no_global_duplicates(self, root):
        seen = {}
        duplicates = []

        for element in root.iter():
            tag = self.local_name(element.tag)

            if not self.is_global_internal_id_tag(tag):
                continue

            if "Id" not in element.attrib:
                continue

            value = element.attrib["Id"]

            if value in seen:
                duplicates.append((value, seen[value], tag))
            else:
                seen[value] = tag

        return duplicates

    def validate_next_pointee(self, root):
        next_element, next_value = self.get_next_pointee_id(root)

        max_global = -1

        for element in root.iter():
            tag = self.local_name(element.tag)

            if self.is_global_internal_id_tag(tag) and "Id" in element.attrib:
                value = self.to_int(element.attrib["Id"])

                if value is not None:
                    max_global = max(max_global, value)

        return next_value > max_global, next_value, max_global

    def merge_selected_tracks(
        self,
        base_als_path,
        added_als_path,
        base_track_map,
        added_track_map,
        selected_base_global_ids,
        selected_added_global_ids,
        output_als_path,
    ):
        base_tree = self.load_xml(base_als_path)
        added_tree = self.load_xml(added_als_path)

        base_root = base_tree.getroot()
        added_root = added_tree.getroot()

        base_tracks_container = self.get_tracks_container(base_root)

        delete_ableton_ids = self.build_tracks_to_delete_from_base(
            base_track_map=base_track_map,
            selected_base_global_ids=selected_base_global_ids,
        )

        for ableton_id in delete_ableton_ids:
            track = self.find_track_by_ableton_id(base_root, ableton_id)

            if track is not None:
                self.remove_track_from_root(base_root, track)

        copy_global_ids = self.build_added_copy_plan(
            base_track_map=base_track_map,
            added_track_map=added_track_map,
            selected_base_global_ids=selected_base_global_ids,
            selected_added_global_ids=selected_added_global_ids,
        )

        next_pointee_element, next_pointee_value = self.get_next_pointee_id(base_root)

        source_ableton_id_to_global_id = self.build_source_ableton_id_to_global_id(
            added_track_map
        )

        base_global_id_to_ableton_id = self.build_global_id_to_ableton_id(
            base_track_map
        )

        selected_base_global_ids = set(str(item) for item in selected_base_global_ids)

        old_to_new_track_ids = {}
        copied_track_elements = []

        next_track_id = self.max_track_id(base_root) + 1

        for global_track_id in copy_global_ids:
            added_track_data = added_track_map.get(global_track_id)

            if not added_track_data:
                continue

            old_ableton_id = str(added_track_data.get("ableton_local_id"))
            source_track = self.find_track_by_ableton_id(added_root, old_ableton_id)

            if source_track is None:
                continue

            copied_track = copy.deepcopy(source_track)
            new_ableton_id = str(next_track_id)
            next_track_id += 1

            copied_track.attrib["Id"] = new_ableton_id
            old_to_new_track_ids[old_ableton_id] = new_ableton_id

            copied_track_elements.append(
                {
                    "global_track_id": global_track_id,
                    "old_ableton_id": old_ableton_id,
                    "new_ableton_id": new_ableton_id,
                    "element": copied_track,
                }
            )

        for copied in copied_track_elements:
            copied_track = copied["element"]

            self.clone_sends_from_destination(copied_track, base_root)

            next_pointee_value = self.remap_global_internal_ids_unique_per_element(
                copied_track,
                next_pointee_value,
            )

            self.remap_track_group_references(
                copied_track=copied_track,
                source_old_track_id_to_new_track_id=old_to_new_track_ids,
                source_ableton_id_to_global_id=source_ableton_id_to_global_id,
                base_global_id_to_ableton_id=base_global_id_to_ableton_id,
                selected_base_global_ids=selected_base_global_ids,
            )

            self.insert_track_in_correct_position(
                base_tracks_container,
                copied_track,
            )

        next_pointee_element.attrib["Value"] = str(next_pointee_value)

        duplicates = self.validate_no_global_duplicates(base_root)
        next_ok, next_value, max_global = self.validate_next_pointee(base_root)

        if duplicates:
            raise RuntimeError(
                f"Merged ALS has duplicate internal IDs: {duplicates[:5]}"
            )

        if not next_ok:
            raise RuntimeError(
                f"NextPointeeId is invalid. Next={next_value}, max={max_global}"
            )

        self.save_xml(base_tree, output_als_path)

        return {
            "output_als_path": str(output_als_path),
            "deleted_ableton_ids": delete_ableton_ids,
            "copied_global_ids": copy_global_ids,
        }