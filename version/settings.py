"""This is module for settings."""
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
import configparser
import os
import logging
import pickle

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


def _get_path():
    """get path."""
    if os.name == 'posix':
        settings_p = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'settings.ini')
        phappypanda_p = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '.happypanda')
    else:
        settings_p = 'settings.ini'
        phappypanda_p = '.happypanda'
    return (settings_p, phappypanda_p)


settings_path, phappypanda_path = _get_path()


def _open_settings_path(path):
    if not os.path.isfile(path):
        open(path, 'x')

_open_settings_path(settings_path)


class Config(configparser.ConfigParser):
    """config class."""

    def __init__(self):
        """init func."""
        super().__init__()

    def read(self, filenames, encoding=None):
        """read func."""
        self.custom_cls_file = filenames
        super().read(filenames, encoding)

    def save(self, encoding='utf-8', space_around_delimeters=True):
        """save func."""
        try:
            if not isinstance(self.custom_cls_file, str) and \
                    hasattr(self.custom_cls_file, '__iter__'):
                for file in self.custom_cls_file:
                    with open(file, 'w', encoding=encoding) as cf:
                        self.write(cf, space_around_delimeters)
            else:
                with open(self.custom_cls_file, 'w') as cf:
                    self.write(cf, space_around_delimeters)
        except PermissionError:  # NOQA
            log_e('Could not save settings: PermissionError')
        except:
            log.exception('Could not save settings')

config = Config()
config.read(settings_path)


def save():
    """save func."""
    config.save()
    ExProperties.save()


def _get_value(key, section, default, config_var):
    """get value from dict with custom method.

    this is helper function to simplify `get` function.
    """
    if key:
        try:
            value = config_var[section][key]
        except KeyError:
            value = default
    else:
        try:
            value = config_var[section]
        except KeyError:
            value = default
    return value


def _normalize_value(value, type_class=None, subtype_class=None):
    """normalize the value."""
    type_class = type_class or str
    if value.lower() == 'false':
        value = False
    elif value.lower() == 'true':
        value = True
    elif value.lower() == 'none':
        value = None
    elif type_class in (list, tuple):
        value = type_class([x for x in value.split('>|<') if x])
    elif subtype_class:
        try:
            value = type_class(value)
        except:
            value = subtype_class(value)
    else:
        value = type_class(value)
    return value


def get(default, section, key=None, type_class=str, subtype_class=None):
    """
    Try to find the given entries in config.

    returning default if none is found. Default type
    is str. Subtype will be used for when try_excepting fails
    """
    value = default
    try:
        value = _get_value(key, section, default, config_var=config)
        try:
            value = _normalize_value(
                value, type_class=type_class, subtype_class=subtype_class)
        except AttributeError:
            pass
        except:
            return default
        return value
    except:
        return default


def set(value, section, key=None):
    """
    Add a new entry in config.

    Remember everything is converted to string
    """
    val_as_str = value
    if section not in config:
        config[section] = {}
    if isinstance(value, (list, tuple)):
        val_as_str = ""
        for n, v in enumerate(value):
            if n == len(value) - 1:
                val_as_str += "{}".format(v)
            else:
                val_as_str += "{}>|<".format(v)

    if key:
        config[section][key] = str(val_as_str)
    else:
        config[section] = str(val_as_str)


class Properties:
    """properties class."""

    pass


class ExProperties(Properties):
    """ex propertiest."""

    # sites
    EHENTAI, NHENTAI = range(2)
    sites = (EHENTAI, NHENTAI,)

    _INFO = {}

    def __init__(self, site=EHENTAI):
        """init func."""
        self.site = site
        if not self._INFO:
            if os.path.exists(phappypanda_path):
                with open(phappypanda_path, 'rb') as f:
                    self.__class__._INFO = pickle.load(f)

    @classmethod
    def save(cls):
        """save."""
        if cls._INFO:
            with open(phappypanda_path, 'wb') as f:
                pickle.dump(cls._INFO, f, 4)

    @property
    def cookies(self):
        """cookies."""
        if self._INFO:
            if self.site in self._INFO:
                return self._INFO[self.site]['cookies']
        return {}

    @cookies.setter
    def cookies(self, c):
        if self.site not in self._INFO:
            self._INFO[self.site] = {}
        self._INFO[self.site]['cookies'] = c

    @property
    def username(self):
        """username."""
        if self._INFO:
            if self.site in self._INFO:
                return self._INFO[self.site]['username']

    @username.setter
    def username(self, us):
        if self.site not in self._INFO:
            self._INFO[self.site] = {}
        self._INFO[self.site]['username'] = us

    @property
    def password(self):
        """password."""
        if self._INFO:
            if self.site in self._INFO:
                return self._INFO[self.site]['password']

    @password.setter
    def password(self, ps):
        if self.site not in self._INFO:
            self._INFO[self.site] = {}
        self._INFO[self.site]['password'] = ps

    def check(self):
        """Return true if usable."""
        if self.site == self.EHENTAI:
            if "ipb_session_id" in self.cookies and "ipb_pass_hash" in self.cookies:
                return 2
            elif 'ipb_session_id' in self.cookies:
                return 1
            else:
                return 0
        elif self.site == self.NHENTAI:
            if "sessionid" in self.cookies:
                return True
        else:
            return True
        return False


class WinProperties(Properties):
    """win properties."""

    def __init__(self):
        """init func."""
        self._resize = None
        self._pos = (0, 0)

    @property
    def resize(self):
        """resize."""
        return self._resize

    @resize.setter
    def resize(self, size):
        assert isinstance(size, list) or isinstance(size, tuple)
        self._resize = tuple(size)

    @property
    def pos(self):
        """pos."""
        return self._pos

    @pos.setter
    def pos(self, point):
        assert isinstance(point, list) or isinstance(point, tuple)
        self._pos = tuple(point)


def win_read(cls, name):
    """Read window properties."""
    assert isinstance(name, str)
    props = WinProperties()
    try:
        props.resize = (int(config[name]['resize.w']),
                        int(config[name]['resize.h']))
        props.pos = (int(config[name]['pos.x']), int(config[name]['pos.y']))
    except KeyError:
        pass
    return props


def win_save(cls, name, winprops=None):
    """
    Save window properties.

    Saves current window properties if no winproperties is passed
    """
    assert isinstance(name, str)
    if not winprops:
        if name not in config:
            config[name] = {}
        config[name]['resize.w'] = str(cls.size().width())
        config[name]['resize.h'] = str(cls.size().height())
        config[name]['pos.x'] = str(cls.pos().x())
        config[name]['pos.y'] = str(cls.pos().y())
    else:
        assert isinstance(winprops, WinProperties), \
            'You must pass a winproperties derived from WinProperties class'

    config.save()
