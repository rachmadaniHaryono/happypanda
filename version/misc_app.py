"""This module contain function used by app module."""
# """
# This file is part of Happypanda.
# Happypanda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Happypanda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
# """
import random
import logging
import scandir
import os

try:
    import app_constants
    import settings
    import gallerydb
except ImportError:
    from . import (
        app_constants,
        settings,
        gallerydb,
    )


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def invoke_first_time_level():
    """invoke first time of certain level."""
    app_constants.INTERNAL_LEVEL = 7
    if app_constants.EXTERNAL_VIEWER_ARGS == '{file}':
        app_constants.EXTERNAL_VIEWER_ARGS = '{$file}'
        settings.set('{$file}', 'Advanced', 'external viewer args')
        settings.save()


def normalize_first_time():
    """normalize for first time."""
    if app_constants.FIRST_TIME_LEVEL != app_constants.INTERNAL_LEVEL:
        settings.set(app_constants.INTERNAL_LEVEL, 'Application', 'first time level')
        settings.save()
    else:
        settings.set(app_constants.vs, 'Application', 'version')


def get_finished_startup_update_text():
    """get update text when startup done."""
    if app_constants.UPDATE_VERSION != app_constants.vs:
        return (
            "Happypanda has been updated!",
            "Don't forget to check out what's new in this version "
            "<a href='https://github.com/Pewpews/happypanda/blob/master/CHANGELOG.md'>"
            "by clicking here!</a>")
    else:
        hello = [
            "Hello!", "Hi!", "Onii-chan!", "Senpai!", "Hisashiburi!", "Welcome!",
            "Okaerinasai!", "Welcome back!", "Hajimemashite!"]
        return (
            "{}".format(random.choice(hello)),
            "Please don't hesitate to report any bugs you find.",
            10)


def set_search_case(b):
    """set search case."""
    app_constants.GALLERY_SEARCH_CASE = b
    settings.set(b, 'Application', 'gallery search case')
    settings.save()


def clean_up_temp_dir():
    """clean temp up dir."""
    try:
        for root, dirs, files in scandir.walk('temp', topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        log_d('Flush temp on exit: OK')
    except:
        log.exception('Flush temp on exit: FAIL')


def clean_up_db():
    """clean up db."""
    try:
        log_i("Analyzing database...")
        gallerydb.GalleryDB.analyze()
        log_i("Closing database...")
        gallerydb.GalleryDB.close()
    except:
        pass


def set_tool_button_attribute(
        tool_button,
        shortcut,
        popup_mode=None,
        menu=None,
        tooltip=None,
        text=None,
        icon=None,
        fixed_width=None,
        clicked_connect_func=None
):
    """set attribute toolbutton."""
    tool_button.setShortcut(shortcut)
    if text is not None:
        tool_button.setText(text)
    if popup_mode is not None:
        tool_button.setPopupMode(popup_mode)
    if tooltip is not None:
        tool_button.setToolTip(tooltip)
    if icon is not None:
        tool_button.setIcon(icon)
    if fixed_width is not None:
        tool_button.setFixedWidth(fixed_width)
    if clicked_connect_func is not None:
        tool_button.clicked.connect(clicked_connect_func)
    if menu is not None:
        tool_button.setMenu(menu)
    return tool_button


def set_action_attribute(
    action,
    triggered_connect_function,
    shortcut=None,
    tool_tip=None,
    status_tip=None,
):
    """set qaction obj attribute."""
    # if triggered_connect_function is not None:
    action.triggered.connect(triggered_connect_function)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tool_tip is not None:
        action.setToolTip(tool_tip)
    if status_tip is not None:
        action.setStatusTip(status_tip)
    return action
