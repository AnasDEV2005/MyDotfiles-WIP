import gi
from fabric_config.utils.icon_resolver import IconResolver

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.wayland import WaylandWindow as Window

gi.require_version("Glace", "0.1")
gi.require_version("Gtk", "3.0")
from gi.repository import Glace, Gtk


class OpenAppsBar(Box):
    def __init__(self):
        self.client_buttons = {}
        super().__init__(spacing=10)
        self.icon_resolver = IconResolver()
        self._manager = Glace.Manager()
        self._manager.connect("client-added", self.on_client_added)

    def on_client_added(self, _, client: Glace.Client):
        client_image = Image()
        client_button = Button(
            name="panel-button",
            image=client_image,
            on_button_press_event=lambda *_: client.activate(),
        )
        self.client_buttons[client.get_id()] = client_button

        client.connect(
            "notify::app-id",
            lambda *_: client_image.set_from_pixbuf(
                self.icon_resolver.get_icon_pixbuf(client.get_app_id(), 24)
            ),
        )

        client.connect(
            "notify::activated",
            lambda *_: client_button.add_style_class("activated")
            if client.get_activated()
            else client_button.remove_style_class("activated"),
        )
        tooltip_image = Image(style="padding-top: 50px;")

        popover = Window(type="popup", anchor="top left", child=tooltip_image)

        client_button.connect(
            "enter-notify-event", self.on_enter, client, tooltip_image, popover
        )
        client_button.connect("leave-notify-event", self.on_leave, popover)

        # client.bind_property("title", client_button, "tooltip-text", 0)
        client.connect("close", lambda *_: self.remove(client_button))
        self.add(client_button)

    def on_enter(self, button: Button, event, client, tooltip_image, popover):
        x = event.x_root

        def capture_callback(pbuf, user_data):
            tooltip_image.set_from_pixbuf(
                pbuf.scale_simple(pbuf.get_width() * 0.15, pbuf.get_height() * 0.15, 2)
            )
            tooltip_image.set_style(
                f"padding-left:{x - (pbuf.get_width() * 0.15) // 2}px; padding-top: 10px;"
            )
            popover.show() if button.is_hovered() else None

        self._manager.capture_client(
            client=client,
            overlay_cursor=False,
            callback=capture_callback,
            user_data=None,
        )

    def on_leave(self, button, event, popover: Gtk.Popover):
        popover.hide()
