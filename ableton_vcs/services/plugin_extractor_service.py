import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


TRACK_TAGS = {
    "MidiTrack",
    "AudioTrack",
    "GroupTrack",
    "ReturnTrack",
    "MasterTrack",
}


PLUGIN_DEVICE_TAGS = {
    "PluginDevice",
    "VstPluginDevice",
    "Vst3PluginDevice",
    "AuPluginDevice",
    "AudioUnitPluginDevice",
}


PLUGIN_NAME_TAGS = [
    "PlugName",
    "PluginName",
    "VstPluginName",
    "Vst3PluginName",
    "AuPluginName",
    "AudioUnitName",
    "ProductName",
]


class PluginExtractorService:
    def local_name(self, tag):
        return tag.split("}")[-1]

    def is_als(self, path):
        return str(path).lower().endswith(".als")

    def load_xml_root(self, path):
        path = Path(path)

        if self.is_als(path):
            with gzip.open(path, "rb") as file:
                xml_data = file.read()

            return ET.fromstring(xml_data)

        return ET.parse(path).getroot()

    def is_bad_plugin_name(self, value):
        if value is None:
            return True

        value = str(value).strip()

        if not value:
            return True

        if value.isdigit():
            return True

        lowered = value.lower()

        if lowered.startswith("audio ") and value.split(" ")[-1].isdigit():
            return True

        if lowered.startswith("midi ") and value.split(" ")[-1].isdigit():
            return True

        return False

    def is_good_text_value(self, value):
        return not self.is_bad_plugin_name(value)

    def get_value_from_descendant(self, parent, tag_names):
        tag_names = set(tag_names)

        for element in parent.iter():
            tag = self.local_name(element.tag)

            if tag not in tag_names:
                continue

            for attribute_name in ["Value", "Name"]:
                value = element.attrib.get(attribute_name)

                if self.is_good_text_value(value):
                    return str(value).strip()

            text = (element.text or "").strip()

            if self.is_good_text_value(text):
                return text

        return ""

    def get_track_name(self, track):
        name = self.get_value_from_descendant(
            track,
            [
                "EffectiveName",
                "UserName",
            ],
        )

        if name:
            return name

        track_id = track.attrib.get("Id", "")
        track_type = self.local_name(track.tag)

        return f"{track_type} {track_id}".strip()

    def is_plugin_device_element(self, element):
        tag = self.local_name(element.tag)

        if tag in PLUGIN_DEVICE_TAGS:
            return True

        if tag.endswith("PluginDevice"):
            return True

        return False

    def detect_plugin_format(self, plugin_element):
        tag = self.local_name(plugin_element.tag)

        tags_inside = {
            self.local_name(element.tag)
            for element in plugin_element.iter()
        }

        if "Vst3" in tag or "Vst3PluginInfo" in tags_inside:
            return "VST3"

        if "Vst" in tag or "VstPluginInfo" in tags_inside:
            return "VST"

        if (
            "Au" in tag
            or "AudioUnit" in tag
            or "AuPluginInfo" in tags_inside
            or "AudioUnitInfo" in tags_inside
        ):
            return "Audio Unit"

        return "Plugin"

    def extract_plugin_name(self, plugin_element):
        name = self.get_value_from_descendant(
            plugin_element,
            PLUGIN_NAME_TAGS,
        )

        if name:
            return name

        fallback = self.get_value_from_descendant(
            plugin_element,
            [
                "DisplayName",
                "DeviceName",
                "Name",
            ],
        )

        if fallback and not self.is_bad_plugin_name(fallback):
            return fallback

        return "Unknown plugin"

    def find_plugin_devices_inside_track(self, track):
        plugin_devices = []

        for element in track.iter():
            if element is track:
                continue

            if self.is_plugin_device_element(element):
                plugin_devices.append(element)

        return plugin_devices

    def extract_plugins_from_als(self, als_path):
        root = self.load_xml_root(als_path)
        rows = []
        seen = set()

        for track in root.iter():
            track_type = self.local_name(track.tag)

            if track_type not in TRACK_TAGS:
                continue

            track_name = self.get_track_name(track)
            track_id = track.attrib.get("Id", "")

            plugin_devices = self.find_plugin_devices_inside_track(track)

            for plugin in plugin_devices:
                plugin_name = self.extract_plugin_name(plugin)
                plugin_format = self.detect_plugin_format(plugin)

                signature = (
                    str(track_id),
                    track_name,
                    plugin_name,
                    plugin_format,
                )

                if signature in seen:
                    continue

                seen.add(signature)

                rows.append(
                    {
                        "track_id": str(track_id),
                        "track_name": track_name,
                        "track_type": track_type,
                        "plugin_name": plugin_name,
                        "plugin_format": plugin_format,
                    }
                )

        return rows