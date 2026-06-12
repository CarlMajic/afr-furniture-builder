from . import header_panel, cafe_panel, bar_panel, lounge_panel, dining_panel


def register():
    header_panel.register()
    cafe_panel.register()
    bar_panel.register()
    lounge_panel.register()
    dining_panel.register()


def unregister():
    dining_panel.unregister()
    lounge_panel.unregister()
    bar_panel.unregister()
    cafe_panel.unregister()
    header_panel.unregister()
