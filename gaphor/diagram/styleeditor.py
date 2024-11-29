from gi.repository import Gdk, Gtk

from gaphor.core.modeling import Presentation
from gaphor.diagram.propertypages import PropertyPageBase, PropertyPages, new_builder


@PropertyPages.register(Presentation)
class StylePropertyPage(PropertyPageBase):
    """A button to open a easy-to-use CSS editor."""

    order = 300
    style_editor = None

    def __init__(self, subject, event_manager):
        super().__init__()
        self.subject = subject
        self.event_manager = event_manager
        self.watcher = subject.watcher() if subject else None
        self.propertypages_builder = new_builder(
            "style-editor",
            signals={
                "open-style-editor": (self._on_open_style_editor,),
            },
        )
        self.has_style_editor = False

    def construct(self):
        if not self.subject:
            return
        assert self.watcher
        return self.propertypages_builder.get_object("style-editor")

    def _on_open_style_editor(self, button):
        if not self.has_style_editor:
            if StylePropertyPage.style_editor:
                StylePropertyPage.style_editor.close()
            StylePropertyPage.style_editor = StyleEditor(
                self.subject, self.close_style_editor
            )
            self.has_style_editor = True
        if StylePropertyPage.style_editor:
            StylePropertyPage.style_editor.present()

    def close_style_editor(self):
        StylePropertyPage.style_editor = None
        self.has_style_editor = False


class StyleEditor:
    def __init__(self, subject, close_callback):
        self.subject = subject
        self.window_builder = Gtk.Builder()
        self.window_builder.add_from_file("gaphor/diagram/styleeditor.ui")
        self.window = None
        self.close_callback = close_callback
        self.color_button = None

    def present(self):
        if self.window is None:
            self.window = self.window_builder.get_object("style-editor")
            self.window.connect("close-request", self.close)
            self.color = self.window_builder.get_object("color")
            self.border_radius = self.window_builder.get_object("border-radius")
            self.background_color = self.window_builder.get_object("background-color")
            self.text_color = self.window_builder.get_object("text-color")
            self.fields()
        self.window.present()

    def fields(self):
        if self.subject.presentation_style.get_style("color"):
            self.color.set_rgba(self.get_color("color"))
        self.color.connect("color-set", self.on_color_set)

        if self.subject.presentation_style.get_style("border-radius"):
            self.border_radius.set_value(
                int(float(self.subject.presentation_style.get_style("border-radius")))
            )
        self.border_radius.connect("value-changed", self.on_border_radius_set)

        if self.subject.presentation_style.get_style("background-color"):
            self.background_color.set_rgba(self.get_color("background-color"))
        self.background_color.connect("color-set", self.on_background_color_set)

        if self.subject.presentation_style.get_style("text-color"):
            self.text_color.set_rgba(self.get_color("text-color"))
        self.text_color.connect("color-set", self.on_text_color_set)

        self.window_builder.get_object("export").connect("clicked", self.on_export)

    def get_color(self, color_type):
        color = self.subject.presentation_style.get_style(color_type)
        rgba = Gdk.RGBA()
        rgba.parse(color)
        return rgba

    def close(self, widget=None):
        if self.window:
            self.window.destroy()
            self.window = None
        self.close_callback()

    def on_color_set(self, widget):
        colors = widget.get_rgba()
        r = int(colors.red * 255)
        g = int(colors.green * 255)
        b = int(colors.blue * 255)
        a = colors.alpha
        self.subject.presentation_style.change_style(
            "color", f"rgba({r}, {g}, {b}, {a})"
        )

    def on_border_radius_set(self, widget):
        self.subject.presentation_style.change_style(
            "border-radius", widget.get_value()
        )

    def on_background_color_set(self, widget):
        colors = widget.get_rgba()
        r = int(colors.red * 255)
        g = int(colors.green * 255)
        b = int(colors.blue * 255)
        a = colors.alpha
        self.subject.presentation_style.change_style(
            "background-color", f"rgba({r}, {g}, {b}, {a})"
        )

    def on_text_color_set(self, widget):
        colors = widget.get_rgba()
        r = int(colors.red * 255)
        g = int(colors.green * 255)
        b = int(colors.blue * 255)
        a = colors.alpha
        self.subject.presentation_style.change_style(
            "text-color", f"rgba({r}, {g}, {b}, {a})"
        )

    def on_export(self, widget):
        self.subject.presentation_style.translate_to_stylesheet()
