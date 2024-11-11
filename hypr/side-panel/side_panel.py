"""
side panel, edited version of the side panel in fabric examples
contains info about the system and a few tools, in webviews
"""

import os
import time
import psutil
import operator
from collections.abc import Iterator
from loguru import logger
from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay
from fabric.widgets.datetime import DateTime
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.webview import WebView
from fabric.widgets.stack import Stack
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.entry import Entry
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.utils import DesktopApp, get_desktop_applications, idle_add, remove_handler, get_relative_path
from fabric.utils import invoke_repeater, get_relative_path, exec_shell_command

#### S I D E   P A N E L ####


class SidePanel(Window):
    @staticmethod
    def bake_progress_bar(name: str = "progress-bar", size: int = 64, **kwargs):
        return CircularProgressBar(
            name=name, min_value=0, max_value=100, line_width=3, size=size, **kwargs
        )
    def bake_bat_bar(name: str = "bat-bar", size: int = 64, **kwargs):
        return CircularProgressBar(
            name="progress-bar", min_value=0, max_value=100, line_style='butt', size=size, **kwargs
        )
    def bake_disk_bar(name: str = "disk-bar", size: int = 64, **kwargs):
        return CircularProgressBar(
            name="progress-bar", min_value=0, max_value=100, pie=True, size=size, **kwargs
        )

    @staticmethod
    def bake_progress_icon(**kwargs):
        return Label(**kwargs).build().add_style_class("progress-icon").unwrap()
    


    def __init__(self, **kwargs):
        super().__init__(
            layer="overlay",
            title="fabric-overlay",
            anchor="top left bottom",
            margin="10px 0px 10px 0px",
            keyboard_mode='on-demand',
            exclusivity="auto",
            size=(500, 800),
            visible=False,
            all_visible=False,
            **kwargs,
        )


## STATUS BARS
#############################################################################################################################
        self.disk_progress = self.bake_disk_bar()
        self.ram_progress = self.bake_progress_bar()
        self.bat_circular = self.bake_bat_bar().build().set_value(42).unwrap()

        self.progress_container = Box(
            name="progress-bar-container",
            spacing=25,
            orientation="v",
            children=[
                Box(
                    children=[
                        Overlay(
                            child=self.disk_progress,
                            overlays=[
                                self.bake_progress_icon(
                                    label="",
                                ),
                                Image(
                                    name="close-svg",
                                    image_file="/home/geronimo/.config/hypr/icons/database.png",
                                    size=27,
                                ),
                            ],
                        ),
                    ],
                ),
                Box(
                    children=[
                        Overlay(
                            child=self.ram_progress,
                            overlays=[
                                self.bake_progress_icon(
                                    label="",
                                    style="margin-right: 4px; text-shadow: 0 0 10px #fff;",
                                ),
                                Image(
                                    name="close-svg",
                                    image_file="/home/geronimo/.config/hypr/icons/cpu.png",
                                    size=27,
                                ),
                            ],
                        )
                    ]
                ),
                Box(
                    children=[
                        Overlay(
                            child=self.bat_circular,
                            overlays=[
                                self.bake_progress_icon(
                                    label="",
                                    style="margin-right: 0px; text-shadow: 0 0 10px #fff, 0 0 18px #fff;",
                                ),
                                Image(
                                    name="close-svg",
                                    image_file="/home/geronimo/.config/hypr/icons/bat.png",
                                    size=27,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
##################### TOOLS STACK ########################################################################3        

## NOTES
############################################################
        self.note = WebView(
            name='notes',
            url = "https://www.rapidtables.com/tools/notepad.html",
            size = (400,900),
        )
        self.window_note = Window(
                name="appslauncher",
                layer="overlay",
                title="fabric-overlay",
                anchor="top left bottom",
                margin="0px 0px 0px 0px",
                keyboard_mode='on-demand',
                exclusivity="auto",
                visible=False,
                all_visible=False,
                size=(400, 800),
                child=self.note,
            )
## CHAT
#############################################################
        self.chat = WebView(
            name='chat',
            url = "https://chatgpt.com",
            size = (400,900),
        )
        self.window_chat = Window(
                name="appslauncher",
                layer="overlay",
                title="fabric-overlay",
                anchor="top left bottom",
                margin="0px 0px 0px 0px",
                keyboard_mode='on-demand',
                exclusivity="auto",
                visible=False,
                all_visible=False,
                size=(400, 800),
                child=self.chat,
            )
## APP LAUNCHER
##############################################################
        self._arranger_handler: int = 0
        self._all_apps = get_desktop_applications()

        self.viewport = Box(name='viewport', spacing=15, orientation="v")
        self.search_entry = Entry(
            name='search',
            placeholder="Search Apps...",
            h_expand=True,
            notify_text=lambda entry, *_: self.arrange_viewport(entry.get_text()),
            on_button_press_event=print,
        )
        self.scrolled_window = ScrolledWindow(
            min_content_size=(300, 320),
            max_content_size=(300, 800),
            child=self.viewport,
        )
        self.appbox = Box(
            name="appbox",
            orientation="v",
            children=[
                    Box(
                        spacing=2,
                        orientation="h",
                        children=[
                            self.search_entry,
                        ],
                    ),
                    # the actual slots holder
                    self.scrolled_window,
                ],
        )
        self.window_apps = Window(
                name="appslauncher",
                layer="overlay",
                title="fabric-overlay",
                anchor="top left bottom",
                margin="0px 0px 0px 0px",
                keyboard_mode='on-demand',
                exclusivity="auto",
                visible=False,
                all_visible=False,
                size=(400, 800),
                child=self.appbox,
            )

##################### TOOLS BUTTONS ########################################################################3        

        self.buttons = Box(
            orientation='v',
            style="margin-top:30px;",
            spacing=30,
            children=[
            Button(name='apps',
                    child=Image(
                        name="apps",
                        image_file="/home/geronimo/.config/hypr/icons/squares-four.png",
                        size=38,
                    ),

                    on_clicked=lambda *_: self.toggle_window_app(),
                ),
            Button(name='note',
                    child=Image(
                        name="apps",
                        image_file="/home/geronimo/.config/hypr/icons/notepad.png",
                        size=38,
                    ),

                    on_clicked=lambda *_: self.toggle_window_note(),
                ),
            Button(name='chat',
                    child=Image(
                        name="apps",
                        image_file="/home/geronimo/.config/hypr/icons/chat-text.png",
                        size=38,
                    ),

                    on_clicked=lambda *_: self.toggle_window_chat(),
                ),
            ]
        )
         


        self.toolbox = Box(
            children=[self.window_apps, self.note, self.chat],
        )
        self.sidebar = Box(
            name="window-inner",
            orientation="v",
            spacing=15,
            children=[self.progress_container,self.buttons],
        )
        self.sidepanel = Box(
                name="maaan",
                orientation='h',
                children=[self.toolbox, self.sidebar],
            )
        self.add(
            self.sidepanel
        )

        self.update_status()
        self.show_all()
        self.toolbox.hide()




## some more functiona
    def update_status(self):
        self.disk_progress.value = psutil.disk_usage('/home').percent
        self.ram_progress.value = psutil.virtual_memory().percent
        if not (bat_sen := psutil.sensors_battery()):
            self.bat_circular.value = 42
        else:
            self.bat_circular.value = bat_sen.percent

        return True

    def get_current_uptime(self):
        uptime = time.time() - psutil.boot_time()
        uptime_days, remainder = divmod(uptime, 86400)
        uptime_hours, remainder = divmod(remainder, 3600)
        # uptime_minutes, _ = divmod(remainder, 60)
        return f"{int(uptime_days)} {'days' if uptime_days > 1 else 'day'}, {int(uptime_hours)} {'hours' if uptime_hours > 1 else 'hour'}"
    
    def toggle_window_chat(self):
        if self.window_chat.is_visible(): self.window_chat.hide()
        elif self.window_note.is_visible(): 
            self.window_note.hide()
            self.window_chat.show()
        elif self.window_apps.is_visible(): 
            self.window_apps.hide()
            self.window_chat.show()
        else: self.window_chat.show()

    def toggle_window_note(self):
        if self.window_note.is_visible(): self.window_note.hide()
        elif self.window_apps.is_visible(): 
            self.window_apps.hide()
            self.window_note.show()
        elif self.window_chat.is_visible(): 
            self.window_chat.hide()
            self.window_note.show()
        else: self.window_note.show()

    def toggle_window_app(self):
        if self.window_apps.is_visible(): self.window_apps.hide()
        elif self.window_note.is_visible(): 
            self.window_note.hide()
            self.window_apps.show()
        elif self.window_chat.is_visible(): 
            self.window_note.hide()
            self.window_apps.show()
        else: self.window_apps.show()



    def arrange_viewport(self, query: str = ""):
        # reset everything so we can filter current viewport's slots...
        # remove the old handler so we can avoid race conditions
        remove_handler(self._arranger_handler) if self._arranger_handler else None

        # remove all children from the viewport
        self.viewport.children = []

        # make a new iterator containing the filtered apps
        filtered_apps_iter = iter(
            [
                app
                for app in self._all_apps
                if query.casefold()
                in (
                    (app.display_name or "")
                    + (" " + app.name + " ")
                    + (app.generic_name or "")
                ).casefold()
            ]
        )
        should_resize = operator.length_hint(filtered_apps_iter) == len(self._all_apps)

        # all aboard...
        # start the process of adding slots with a lazy executor
        # using this method makes the process of adding slots way more less
        # resource expensive without blocking the main thread and resulting in a lock
        self._arranger_handler = idle_add(
            lambda *args: self.add_next_application(*args)
            or (self.resize_viewport() if should_resize else False),
            filtered_apps_iter,
            pin=True,
        )

        return False

    def add_next_application(self, apps_iter: Iterator[DesktopApp]):
        if not (app := next(apps_iter, None)):
            return False

        self.viewport.add(self.bake_application_slot(app))
        return True

    def resize_viewport(self):
        self.scrolled_window.set_min_content_width(
            self.viewport.get_allocation().width  # type: ignore
        )
        return False

    def bake_application_slot(self, app: DesktopApp, **kwargs) -> Button:
        return Button(
            name='appslot',
            child=Box(
                orientation="h",
                spacing=12,
                children=[
                    Image(pixbuf=app.get_icon_pixbuf(), h_align="start", size=32),
                    Label(
                        label=app.display_name or "Unknown",
                        v_align="center",
                        h_align="center",
                    ),
                ],
            ),
            tooltip_text=app.description,
            on_clicked=lambda *_: (app.launch(), self.window_apps.hide()),
            **kwargs,
        )                
        

if __name__ == "__main__":
    side_panel = SidePanel()
    app = Application("side-panel", side_panel)
    app.set_stylesheet_from_file(get_relative_path("side_panel.css"))

    app.run()
