import gzip
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


TRACK_TAGS = {
    "AudioTrack",
    "MidiTrack",
    "ReturnTrack",
    "GroupTrack",
}


SKIP_TAGS = {
    # Display / naming / visual metadata
    "Name",
    "Color",
    "Annotation",

    # View state
    "IsFolded",
    "TrackUnfolded",
    "ViewData",
    "ViewStateSessionTrackWidth",
    "ScrollerTimePreserver",
    "TimeSelection",
    "SelectedDevice",
    "SelectedEnvelope",
    "SelectedToolPanel",
    "SelectedTransformationName",
    "SelectedGeneratorName",
    "SelectedMidiEditorMode",
    "LastSelectedTimeableIndex",
    "LastSelectedClipEnvelopeIndex",
    "PreferredContentViewMode",
    "IsContentSelectedInDocument",

    # Temporary performance / recording state
    "SoloSink",
    "Recorder",
    "IsArmed",
    "Arm",

    # Freeze/cache state
    "FreezeSequencer",
    "NeedRefreeze",
    "NeedArrangerRefreeze",

    # Preset/browser/script state
    "LastPresetRef",
    "LockedScripts",

    # Absolute file metadata that can change without audio content changing
    "Path",
    "LastModDate",
}


SKIP_ATTRIBUTES = {
    "Id",
    "LomId",
    "LomIdView",
    "PointeeId",
    "AutomationTargetId",
    "ModulationTargetId",
    "NoteId",
}


class AlsTrackService:
    def find_main_als_file(self, project_path):
        project_path = Path(project_path)
        als_files = sorted(project_path.glob("*.als"))

        if not als_files:
            raise FileNotFoundError("No .als file found in selected Ableton project folder.")

        return als_files[0]

    def load_als_xml_root(self, als_path):
        als_path = Path(als_path)

        with gzip.open(als_path, "rb") as file:
            xml_data = file.read()

        return ET.fromstring(xml_data)

    def local_name(self, element):
        if "}" in element.tag:
            return element.tag.split("}", 1)[1]

        return element.tag

    def get_value_from_descendant(self, parent_element, tag_name):
        for element in parent_element.iter():
            if self.local_name(element) == tag_name:
                value = element.attrib.get("Value")

                if value is not None:
                    return value

        return None

    def extract_track_name(self, track_element):
        effective_name = self.get_value_from_descendant(track_element, "EffectiveName")

        if effective_name:
            return effective_name

        user_name = self.get_value_from_descendant(track_element, "UserName")

        if user_name:
            return user_name

        track_type = self.local_name(track_element)
        local_id = track_element.attrib.get("Id", "unknown")

        return f"{track_type} {local_id}"

    def extract_track_color(self, track_element):
        color = self.get_value_from_descendant(track_element, "Color")

        if color is None:
            return ""

        return str(color)

    def extract_parent_group_local_id(self, track_element):
        track_group_id = self.get_value_from_descendant(track_element, "TrackGroupId")

        if track_group_id is None:
            return None

        track_group_id = str(track_group_id)

        if track_group_id == "-1":
            return None

        return track_group_id

    def extract_tracks_from_als(self, als_path):
        root = self.load_als_xml_root(als_path)
        tracks = []

        for element in root.iter():
            tag_name = self.local_name(element)

            if tag_name not in TRACK_TAGS:
                continue

            ableton_local_id = element.attrib.get("Id")

            if ableton_local_id is None:
                continue

            tracks.append(
                {
                    "ableton_local_id": str(ableton_local_id),
                    "track_type": tag_name,
                    "track_name": self.extract_track_name(element),
                    "track_color": self.extract_track_color(element),
                    "parent_group_local_id": self.extract_parent_group_local_id(element),
                    "content_fingerprint": self.build_content_fingerprint(element),
                }
            )

        return tracks

    def extract_current_project_tracks(self, project_path):
        als_path = self.find_main_als_file(project_path)

        return {
            "als_path": str(als_path),
            "tracks": self.extract_tracks_from_als(als_path),
        }

    def build_content_fingerprint(self, track_element):
        normalized = self.normalize_track_element(track_element)
        serialized = json.dumps(
            normalized,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def normalize_track_element(self, element, parent_path=None):
        if parent_path is None:
            parent_path = []

        tag_name = self.local_name(element)
        path = parent_path + [tag_name]

        if self.should_skip_element(tag_name, path):
            return None

        normalized = {
            "tag": tag_name,
        }

        attributes = self.normalize_attributes(element.attrib)

        if attributes:
            normalized["attributes"] = attributes

        text = (element.text or "").strip()

        if text:
            normalized["text"] = text

        children = []

        for child in list(element):
            normalized_child = self.normalize_track_element(child, path)

            if normalized_child is not None:
                children.append(normalized_child)

        if children:
            normalized["children"] = children

        return normalized

    def normalize_attributes(self, attributes):
        normalized = {}

        for key, value in attributes.items():
            if key in SKIP_ATTRIBUTES:
                continue

            if key.endswith("Id"):
                continue

            normalized[key] = str(value)

        return normalized

    def should_skip_element(self, tag_name, path):
        if tag_name in SKIP_TAGS:
            return True

        # Ableton internal id wrappers/counters.
        if tag_name in {
            "Pointee",
            "AutomationTarget",
            "ModulationTarget",
            "NextPointeeId",
            "NextId",
            "NextColorIndex",
        }:
            return True

        # Track-level on/off should NOT count as a track version change.
        # Clip Disabled is not removed here, so clip on/off still counts.
        if tag_name == "On":
            if "Mixer" in path or "MainSequencer" in path:
                return True

        # Solo should not count.
        if tag_name == "Solo":
            return True

        # Recording arm should not count.
        if tag_name in {"Arm", "IsArmed"}:
            return True

        return False