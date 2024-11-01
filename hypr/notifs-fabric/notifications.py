from typing import cast

from fabric import Application
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.image import Image
from fabric.widgets.button import Button
from fabric.widgets.wayland import WaylandWindow
from fabric.notifications import Notifications, Notification
from fabric.utils import invoke_repeater, get_relative_path

from gi.repository import GdkPixbuf


NOTIFICATION_WIDTH = 360
NOTIFICATION_IMAGE_SIZE = 64
NOTIFICATION_TIMEOUT = 10 * 1000  # 10 seconds

applist=['vesktop', 'flameshot', 'pipewire-pulse', 'pipewire', 'brave']
class NotificationWidget(Box):
    def __init__(self, notification: Notification, **kwargs):
        super().__init__(
            size=(NOTIFICATION_WIDTH, -1),
            name="notification",
            spacing=0,
            orientation="h",
            **kwargs,
        )

        self._notification = notification

        body_container = Box(spacing=4, orientation="h")

        if image_pixbuf := self._notification.image_pixbuf:
            if self._notification.app_name == "vesktop":
                self.add(Image(
                        name="notificationvesktop",
                        pixbuf=image_pixbuf.scale_simple(
                            NOTIFICATION_IMAGE_SIZE,
                            NOTIFICATION_IMAGE_SIZE,
                            GdkPixbuf.InterpType.BILINEAR,
                        )))
        if image_pixbuf := self._notification.image_pixbuf:
            if self._notification.app_name == "brave":
                self.add(Image(
                        name="notificationbrave",
                        pixbuf=image_pixbuf.scale_simple(
                            NOTIFICATION_IMAGE_SIZE,
                            NOTIFICATION_IMAGE_SIZE,
                            GdkPixbuf.InterpType.BILINEAR,
                        )))
        if image_pixbuf := self._notification.image_pixbuf:
            if self._notification.app_name == "flameshot":
                self.add(Image(
                        name="notificationflameshot",
                        pixbuf=image_pixbuf.scale_simple(
                            NOTIFICATION_IMAGE_SIZE,
                            NOTIFICATION_IMAGE_SIZE,
                            GdkPixbuf.InterpType.BILINEAR,
                        )))
            
            

        self.body = self.bodbox= Box(                
                name='notificationbox',
                spacing=4,
                orientation="v",
                children=[
                    # a box for holding both the "summary" label and the "close" button
                    Box(
                        orientation="h",
                        children=[
                            Label(
                                label=self._notification.summary,
                                ellipsization="middle",
                            )
                            .build()
                            .add_style_class("summary")
                            .unwrap(),
                        ],
                        h_expand=True,
                        v_expand=True,
                    )
                    # add the "close" button
                    .build(
                        lambda box, _: box.pack_end(
                            Button(
                                name='close',
                                child=Label(
                                    name="close-symbolic",
                                    label='☒',
                                ),
                                v_align="center",
                                h_align="end",
                                on_clicked=lambda *_: self._notification.close(),
                            ),
                            False,
                            False,
                            0,
                        )
                    ),
                    Label(
                        label=self._notification.body,
                        line_wrap="word-char",
                        v_align="start",
                        h_align="start",
                    )
                

                    .build()
                    .add_style_class("body")
                    .unwrap(),
                ],
                h_expand=True,
                v_expand=True,
            )
        if self._notification.app_name in applist:
            for i in applist:
                if self._notification.app_name == i: self.body.set_name('notification'+i)
        if len(self._notification.body)>25: 
                        self.body.children[1].set_label(self._notification.body[:25]+'...')
        self.add(self.body)

        if actions := self._notification.actions:
            self.body.add(
                Box(
                    name='action',
                    spacing=4,
                    orientation="h",
                    children=[
                        Button(
                            name='actiobutton',
                            h_expand=True,
                            v_expand=True,
                            label=action.label,
                            on_clicked=lambda *_, action=action: action.invoke(),
                        )
                        for action in actions
                    ],
                )
            )


        # destroy this widget once the notification is closed
        self._notification.connect(
            "closed",
            lambda *_: (
                parent.remove(self) if (parent := self.get_parent()) else None,  # type: ignore
                self.destroy(),
            ),
        )

        # automatically close the notification after the timeout period
        invoke_repeater(
            NOTIFICATION_TIMEOUT,
            lambda: self._notification.close("expired"),
            initial_call=False,
        )


if __name__ == "__main__":
    app = Application(
        "notifications",
        WaylandWindow(
            margin="8px 8px 8px 8px",
            anchor="top right",
            child=Box(
                size=2,  # so it's not ignored by the compositor
                spacing=4,
                orientation="v",
            ).build(
                lambda viewport, _: Notifications(
                    on_notification_added=lambda notifs_service, nid: viewport.add(
                        NotificationWidget(
                            cast(
                                Notification,
                                notifs_service.get_notification_from_id(nid),
                            )
                        )
                    )
                )
            ),
            visible=True,
            all_visible=True,
        ),
    )

    app.set_stylesheet_from_file(get_relative_path("./style.css"))

    app.run()
