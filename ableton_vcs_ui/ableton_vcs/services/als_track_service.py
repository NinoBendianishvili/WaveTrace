import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


TRACK_TAGS = {
    "AudioTrack",
    "MidiTrack",
    "ReturnTrack",
    "GroupTrack",
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
                    "parent_group_local_id": self.extract_parent_group_local_id(element),
                }
            )

        return tracks

    def extract_current_project_tracks(self, project_path):
        als_path = self.find_main_als_file(project_path)

        return {
            "als_path": str(als_path),
            "tracks": self.extract_tracks_from_als(als_path),
        }