import psutil
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.overlay import Overlay
from fabric.widgets.eventbox import EventBox
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.system_tray.widgets import SystemTray
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import Language, ActiveWindow, Workspaces, WorkspaceButton
from fabric.utils import (
    FormattedString,
    bulk_replace,
    invoke_repeater,
    get_relative_path,
    exec_shell_command
)

AUDIO_WIDGET = True

if AUDIO_WIDGET is True:
    try:
        from fabric.audio.service import Audio
    except Exception as e:
        print(e)
        AUDIO_WIDGET = False

# i havent touched volume stuff, ion rly need it

class VolumeWidget(Box):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio = Audio()

        self.progress_bar = CircularProgressBar(
            name="volume-progress-bar", pie=True, size=24
        )

        self.event_box = EventBox(
            events="scroll",
            child=Overlay(
                child=self.progress_bar,
                overlays=Label(
                    label="",
                    style="margin: 0px 6px 0px 0px; font-size: 12px",  # to center the icon glyph
                ),
            ),
        )

        self.audio.connect("notify::speaker", self.on_speaker_changed)
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        self.show_all()
    def on_scroll(self, _, event):
        match event.direction:
            case 0:
                self.audio.speaker.volume += 8
            case 1:
                self.audio.speaker.volume -= 8
        return

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return
        self.progress_bar.value = self.audio.speaker.volume / 100
        self.audio.speaker.bind(
            "volume", "value", self.progress_bar, lambda _, v: v / 100
        )
        return
    
# the top bar class

class StatusBar(Window):
    @staticmethod
    def power_menu(self):
        exec_shell_command('source ~/.config/hypr/myvenv/bin/activate && python ~/.config/hypr/power-menu/powermenu.py')

    def __init__(
        self,
    ):
        super().__init__(
            name="bar",
            layer="top",
            anchor="left top right",
            margin="10px 10px -2px 10px",
            exclusivity="auto",
            visible=False,
            all_visible=False,
        )
        self.workspaces = Workspaces(       # workspaces
            name="workspaces",
            spacing=4,
            buttons_factory=lambda ws_id: WorkspaceButton(id=ws_id, label=None),
        )
        self.active_window = ActiveWindow(name="hyprland-window")  # the middle title
        self.language = Language(
            formatter=FormattedString(
                "{replace_lang(language)}",
                replace_lang=lambda lang: bulk_replace(
                    lang,
                    (r".*Eng.*", r".*Ar.*"),
                    ("ENG", "ARA"),
                    regex=True,
                ),
            ),
            name="hyprland-window",
        )

        # the status info stuff + tray
        self.date_time = DateTime(name="date-time")
        self.system_tray = SystemTray(name="system-tray", spacing=4)


        self.cpu_progress_bar = CircularProgressBar(
            name="cpu-progress-bar", size=24, line_style='butt'
        )
        self.progress_bars_overlay = Overlay(
            child=self.cpu_progress_bar,
            overlays=[
                Label("", style="margin: 0px 6px 0px 0px; font-size: 12px"),
            ],
        )

        self.status_container = Box(
            name="widgets-container",
            spacing=4,
            orientation="h",
            children=self.progress_bars_overlay,
        )
        self.status_container.add(VolumeWidget()) if AUDIO_WIDGET is True else None



        # putting it all inside the side panel class        
      

        self.children = CenterBox(
            name="bar-inner",
            start_children=Box(
                name="start-container",
                spacing=4,
                orientation="h",
                children=self.workspaces,
            ),
            center_children=Box(
                name="center-container",
                spacing=4,
                orientation="h",
                children=self.active_window,
            ),
            end_children=Box(
                name="end-container",
                spacing=4,
                orientation="h",
                children=[
                    self.status_container,
                    self.system_tray,
                    self.date_time,
                    self.language,
                ],
            ),
        )

        invoke_repeater(1000, self.update_progress_bars)

        self.show_all()

    def update_progress_bars(self):
        self.cpu_progress_bar.value = psutil.cpu_percent() / 100
        return True

# running
if __name__ == "__main__":
    bar = StatusBar()
    app = Application("bar", bar)
    app.set_stylesheet_from_file(get_relative_path("bar.css"))

    app.run()
