from __future__ import annotations

import importlib.resources
import textwrap

from gaphor.core.modeling.base import Base
from gaphor.core.modeling.event import AttributeUpdated
from gaphor.core.modeling.properties import attribute
from gaphor.core.styling import CompiledStyleSheet

SYSTEM_STYLE_SHEET = (importlib.resources.files("gaphor") / "diagram.css").read_text(
    "utf-8"
)

DEFAULT_STYLE_SHEET = textwrap.dedent(
    """\
    diagram {
     /* line-style: sloppy 0.3; */
    }
    """
)


class StyleSheet(Base):
    _compiled_style_sheet: CompiledStyleSheet

    def __init__(self, id=None, model=None):
        super().__init__(id, model)
        self._style_elements = {}
        self._system_font_family = "sans"
        self.compile_style_sheet()

    colorPickerResult: attribute[str] = attribute("colorPickerResult", str, "")
    styleSheet: attribute[str] = attribute("styleSheet", str, DEFAULT_STYLE_SHEET)
    naturalLanguage: attribute[str] = attribute("naturalLanguage", str)

    @property
    def style_elements(self) -> dict:
        return self._style_elements

    def get_style(self, key: str, style: str) -> str | None:
        elem: dict | None = self.style_elements.get(key)
        if elem is not None:
            return elem.get(style)
        return None

    @property
    def system_font_family(self) -> str:
        return self._system_font_family

    @system_font_family.setter
    def system_font_family(self, font_family: str):
        self._system_font_family = font_family
        self.compile_style_sheet()

    def compile_style_sheet(self) -> None:
        self._compiled_style_sheet = CompiledStyleSheet(
            SYSTEM_STYLE_SHEET,
            f"diagram {{ font-family: {self._system_font_family} }}",
            self.colorPickerResult + self.styleSheet,
        )

    def new_compiled_style_sheet(self) -> CompiledStyleSheet:
        return self._compiled_style_sheet.copy()

    def postload(self):
        super().postload()
        self.recover_style_element()
        self.compile_style_sheet()

    def handle(self, event):
        # Ensure compiled style sheet is always up-to-date:
        if (
            isinstance(event, AttributeUpdated)
            and event.property is StyleSheet.styleSheet
        ):
            self.compile_style_sheet()

        super().handle(event)

    def recover_style_element(self):
        self.styleSheet += (
            "\n" + self.colorPickerResult if self.colorPickerResult else ""
        )
        self.colorPickerResult = ""

    def update_style_element(self):
        temp = ""
        for k, v in self.style_elements.items():
            nested_items = "; ".join(f"{x}: {z}" for x, z in v.items())
            nested_items += ";"
            temp += f"{k} {{{nested_items}}}\n"
        return temp

    def change_style_element(self, elem: str, style: str, value: str):
        self.style_elements[elem][style] = value
        self.colorPickerResult = self.update_style_element()
        self.compile_style_sheet()

    def new_style_element(self, elem: str):
        self.style_elements[elem] = {}

    def delete_style_element(self, elem: str):
        if self.style_elements.get(elem):
            self.style_elements.pop(elem)
            self.colorPickerResult = self.update_style_element()
            self.compile_style_sheet()
            return True
        return False

    def change_name_style_element(self, elem: str, new_elem: str):
        if self.style_elements.get(elem):
            self.style_elements.update({new_elem: self.style_elements.pop(elem)})
            self.colorPickerResult = self.update_style_element()
            self.compile_style_sheet()

    def translate_to_stylesheet(self, elem: str):
        if elem_v := self.style_elements.get(elem):
            nested_items = "; ".join(f"{k}: {v}" for k, v in elem_v.items())
            nested_items += ";"
            self.styleSheet += "\n" + f"{elem} {{{nested_items}}}\n"
            return self.delete_style_element(elem)
        return False
