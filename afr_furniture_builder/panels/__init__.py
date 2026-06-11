from . import cafe_panel, bar_panel, lounge_panel


def register():
    cafe_panel.register()
    bar_panel.register()
    lounge_panel.register()


def unregister():
    lounge_panel.unregister()
    bar_panel.unregister()
    cafe_panel.unregister()
