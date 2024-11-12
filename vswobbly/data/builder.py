import json
from dataclasses import dataclass
from typing import Any

from vstools import (FieldBased, FieldBasedT, FileNotExistsError,
                     FileWasNotFoundError, SPath, SPathLike)

from ..components import (CombedFrames, CustomList, CustomLists, Decimations,
                          FieldMatches, FreezeFrame, FreezeFrames,
                          InterlacedFade, InterlacedFades, Preset, Presets,
                          Section, Sections, WobblyVideo)
from ..data.parse import WobblyParser
from ..data.validation import WobblyValidator
from ..exceptions import NotAWobblyFileError, WobblyParseError
from ..types import FilteringPositionEnum
from ..util import to_snake_case

__all__ = [
    'WobblyBuilder'
]


@dataclass
class WobblyBuilder:
    """Builder class for constructing WobblyParser instances."""

    file_path: SPath
    _data: dict[str, Any] | None = None

    def __init__(self, file_path: SPathLike) -> None:
        self.file_path = SPath(file_path)

    def build(self) -> WobblyParser:
        """Build a WobblyParser instance."""

        self._check_file_path()
        self._load_data()

        WobblyValidator.validate_version(self._data)
        WobblyValidator.validate_json_structure(self._data)

        video_data = self._build_video_data()
        field_order = self._build_field_order()
        video_data.work_clip = field_order.apply(video_data.work_clip)

        return WobblyParser(
            file_path=SPath(self.file_path),
            work_clip=video_data.work_clip,
            video_data=video_data,
            field_order=field_order,
            **self._parse_data()
        )

    def _check_file_path(self) -> None:
        """Check if the file path is valid."""

        if not self.file_path.exists():
            raise FileWasNotFoundError(f"File path does not exist: \'{self.file_path}\'", self)

        if not self.file_path.is_file():
            raise FileNotExistsError(f"File path is not a file: \'{self.file_path}\'", self)

        if not self.file_path.suffix == '.wob':
            raise NotAWobblyFileError("You must provide a wobbly file!", self)

        # We check for 2 bytes because wibbly writes 2 bytes when initializing
        if self.file_path.get_size() <= 2:
            raise WobblyParseError(f"File is empty: \'{self.file_path}\'", self)

    def _load_data(self) -> None:
        """Load the wobbly data."""

        with open(self.file_path, 'r') as file:
            self._data = json.load(file)

    def _build_video_data(self) -> WobblyVideo:
        return WobblyVideo(
            SPath(self.file_path).as_posix(),
            self._data
        )

    def _build_field_order(self) -> FieldBasedT:
        vivtc_params = self._data.get('vfm parameters', {})
        order = bool(vivtc_params.get('order', 1))

        return FieldBased.from_param(order)

    def _parse_data(self) -> dict[str, Any]:
        """Parse the wobbly data into their respective component classes."""

        parsed_data = self._parse_components({
            Presets.wob_json_key(): ('presets', Presets, Preset),
            FieldMatches.wob_json_key(): ('field_matches', FieldMatches, str),
            CombedFrames.wob_json_key(): ('combed_frames', CombedFrames, int),
            Decimations.wob_json_key(): ('decimations', Decimations, int),
            Sections.wob_json_key(): ('sections', Sections, Section),
            InterlacedFades.wob_json_key(): ('interlaced_fades', InterlacedFades, InterlacedFade),
            CustomLists.wob_json_key(): ('custom_lists', CustomLists, CustomList),
            FreezeFrames.wob_json_key(): ('freeze_frames', FreezeFrames, FreezeFrame),
        })

        self._build_orphan_frames(parsed_data)

        return parsed_data

    def _parse_components(self, component_map: dict[str, tuple[str, type, type]]) -> dict[str, Any]:
        """Parse each component from the wobbly data."""

        parsed_data = {}

        for wob_key, (attr_name, container_class, item_class) in component_map.items():
            if not self._should_parse_component(wob_key):
                continue

            data = self._data[wob_key]
            processed_items = self._get_processed_items(data, item_class)
            parsed_data[attr_name] = container_class(processed_items)

        return parsed_data

    def _should_parse_component(self, wob_key: str) -> bool:
        """Check if component should be parsed."""

        return wob_key in self._data and self._data[wob_key]

    def _get_processed_items(self, data: list, item_class: type) -> list:
        """Get processed items based on data type and item class."""

        if item_class == Section:
            return self._process_sections(data)

        if isinstance(data[0], dict):
            return self._process_dict_items(data, item_class)

        if isinstance(data[0], list):
            return self._process_list_items(data, item_class)

        return self._process_simple_items(data, item_class)

    def _process_sections(self, data: list[dict]) -> list[Section]:
        """Process sections and handle their presets."""

        preset_lookup = self._build_preset_lookup()
        processed_items = []

        for section in data:
            section_dict = self._to_snake_case(section)
            section_presets = []

            for preset_list in section_dict.get('presets', []):
                if isinstance(preset_list, str):
                    if preset_list in preset_lookup:
                        section_presets.append(preset_lookup[preset_list])
                elif isinstance(preset_list, list):
                    section_presets.extend(preset_lookup[p] for p in preset_list if p in preset_lookup)

            section_dict['presets'] = section_presets
            processed_items.append(Section(**section_dict))

            if not section_presets:
                continue

            self._add_section_presets_to_custom_lists(section_dict, section_presets, data)

        return processed_items

    def _build_preset_lookup(self) -> dict[str, Preset]:
        """Build lookup dictionary for presets."""

        all_presets = self._data.get('presets', [])

        return {
            p['name']: Preset(
                name=self._to_snake_case(p['name']),
                **{k: v for k, v in p.items() if k != 'name'}
            )
            for p in all_presets
        }

    def _has_valid_presets(self, section_dict: dict) -> bool:
        """Check if section has valid presets."""

        return bool(section_dict.get('presets', []))

    def _add_section_presets_to_custom_lists(
        self,
        section_dict: dict,
        presets: list[Preset],
        all_sections: list[dict]
    ) -> None:
        """Add section presets to custom lists."""

        if 'custom lists' not in self._data:
            self._data['custom lists'] = []

        start = section_dict['start']
        section_idx = next(i for i, s in enumerate(all_sections) if s['start'] == start)
        end = self._get_section_end(section_idx, all_sections)

        for preset in presets:
            self._data['custom lists'].append({
                'name': f"section_{start}_{end}_{preset.name}",
                'preset': preset,
                'position': FilteringPositionEnum.PRE_DECIMATE,
                'frames': [(start, end)]
            })

    def _get_section_end(self, section_idx: int, all_sections: list[dict]) -> int:
        """Get end frame for section."""

        if section_idx < len(all_sections) - 1:
            return all_sections[section_idx + 1]['start'] - 1

        return len(self._data.get('field matches', []))

    def _process_dict_items(self, data: list[dict], item_class: type) -> list:
        """Process dictionary items into their respective dataclass instances."""

        if item_class == CustomList:
            preset_lookup = self._build_preset_lookup()

            return [
                item_class(
                    **{
                        **{to_snake_case(k): v for k, v in item.items() if k != 'preset' and k != 'frames'},
                        'preset': preset_lookup.get(item['preset'].name if isinstance(item['preset'], Preset) else item['preset']),
                        'frames': [tuple(frame) for frame in item['frames']]
                    }
                )
                for item in data
            ]

        return [
            item_class(**{to_snake_case(k): v for k, v in item.items()})
            for item in data
        ]

    def _process_list_items(self, data: list[list], item_class: type) -> list:
        """Process list items into their respective dataclass instances."""

        if item_class == FreezeFrame:
            return [item_class(first=item[0], last=item[1], replacement=item[2]) for item in data]

        return [item_class(**{'frames': item}) for item in data]

    def _process_simple_items(self, data: list, item_class: type) -> list:
        """Process simple type items (int, str, etc.)."""

        return [item_class(x) for x in data]

    def _to_snake_case(self, item: dict[Any, Any] | str) -> dict[Any, Any] | str:
        """Convert dictionary keys from space-separated to snake_case."""

        if isinstance(item, str):
            return to_snake_case(item)

        return {
            to_snake_case(k) if isinstance(v, str) else k: to_snake_case(v) if isinstance(v, str) else v
            for k, v in item.items()
        }

    def _build_orphan_frames(self, parsed_data: dict) -> None:
        """Add orphan frames if both sections and field matches exist."""

        from ..components import OrphanFrames

        sections = parsed_data.get(Sections.wob_json_key())
        matches = parsed_data.get('field_matches')

        if not sections or not matches:
            return

        parsed_data['orphan_frames'] = OrphanFrames.from_sections(sections, matches)
