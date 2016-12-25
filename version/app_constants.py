"""App constants.

Contains constants to be used by several modules.
"""
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


import os
import sys
import enum

try:  # pragma: no cover
    import settings
    from database import db_constants
except ImportError:
    from . import settings
    from .database import db_constants

# Version number
vs = '0.30'
DEBUG = False


def _get_os_name():
    """get os name"""
    if sys.platform.startswith('darwin'):
        return "darwin"
    elif os.name == 'nt':
        return "windows"
    elif os.name == 'posix':
        return "linux"

OS_NAME = _get_os_name()

APP_RESTART_CODE = 0

get = settings.get


def _get_dirs():
    """get tuple of dirs."""
    posix_program_dir = os.path.dirname(os.path.realpath(__file__))
    if os.name == 'posix':
        bin_dir = os.path.join(posix_program_dir, 'bin')
        static_dir = os.path.join(posix_program_dir, '../res')
        temp_dir = os.path.join(posix_program_dir, 'temp')
    else:
        cwd = os.getcwd()
        bin_dir = os.path.join(cwd, 'bin')
        static_dir = os.path.join(cwd, "res")
        temp_dir = os.path.join('temp')
    return posix_program_dir, bin_dir, static_dir, temp_dir

posix_program_dir, bin_dir, static_dir, temp_dir = _get_dirs()
# path to unrar tool binary
unrar_tool_path = get('', 'Application', 'unrar tool path')

# from utils.py
IMG_FILES = ('.jpg', '.bmp', '.png', '.gif', '.jpeg')
IMG_FILTER = '*.jpg *.bmp *.png *.jpeg'


def _get_archive_files_and_file_filter(unrar_tool):
    """get archive file and file filter."""
    archive_files = ('.zip', '.cbz', '.rar', '.cbr')
    file_filter = '*.zip *.cbz *.rar *.cbr'
    if not unrar_tool:
        file_filter = '*.zip *.cbz'
        archive_files = ('.zip', '.cbz')
    return archive_files, file_filter


ARCHIVE_FILES, FILE_FILTER = _get_archive_files_and_file_filter(unrar_tool=unrar_tool_path)

# type of download needed by download manager for each site parser
# NOTE define here if any new type will be supported in the future.
DOWNLOAD_TYPE_ARCHIVE = 0
DOWNLOAD_TYPE_TORRENT = 1
DOWNLOAD_TYPE_OTHER = 2
DOWNLOAD_TYPE_DICT_CONSTANT = {
    DOWNLOAD_TYPE_ARCHIVE: 'Archive',
    DOWNLOAD_TYPE_TORRENT: 'Torrent',
    DOWNLOAD_TYPE_OTHER: 'Other'
}

# VALID gallery category
VALID_GALLERY_CATEGORY = (
    'Doujinshi',
    'Manga',
    'Artist CG',
    'Game CG',
    'Western',
    'Non-H',
    'Image Set',
    'Cosplay',
    'Miscellaneous',
    'Private'
)

# default stylesheet path
default_stylesheet_path = os.path.join(static_dir, "style.css")
user_stylesheet_path = ""

INTERNAL_LEVEL = 7
FIRST_TIME_LEVEL = get(7, 'Application', 'first time level', int)
UPDATE_VERSION = get('0.25', 'Application', 'version', str)
FORCE_HIGH_DPI_SUPPORT = get(False, 'Advanced', 'force high dpi support', bool)

# sizes
MAIN_W = 1061  # main window
MAIN_H = 650  # main window
SIZE_FACTOR = get(10, 'Visual', 'size factor', int)
GRID_SPACING = get(15, 'Visual', 'grid spacing', int)
LISTBOX_H_SIZE = 190
LISTBOX_W_SIZE = 950
GRIDBOX_LBL_H = 60
THUMB_H_SIZE = 190 + SIZE_FACTOR
THUMB_W_SIZE = 133 + SIZE_FACTOR

THUMB_DEFAULT = (THUMB_W_SIZE, THUMB_H_SIZE)
THUMB_SMALL = (140, 93)

# Columns
COLUMNS = tuple(range(11))
TITLE = 0
ARTIST = 1
DESCR = 2
TAGS = 3
TYPE = 4
FAV = 5
CHAPTERS = 6
LANGUAGE = 7
LINK = 8
PUB_DATE = 9
DATE_ADDED = 10


@enum.unique
class ViewType(enum.IntEnum):
    """view type."""

    Default = 1
    Addition = 2
    Duplicate = 3


@enum.unique
class ProfileType(enum.Enum):
    """profile type."""

    Default = 1
    Small = 2

# Application
SYSTEM_TRAY = None
NOTIF_BAR = None
NOTIF_BUBBLE = None
STAT_MSG_METHOD = None
GENERAL_THREAD = None
WHEEL_SCROLL_EFFECT = 10
DOWNLOAD_MANAGER = None

# image paths
SAMPLE_PATH = os.path.join(static_dir, "sample.png")
SORT_PATH = os.path.join(static_dir, "sort.png")
GALLERY_ICO_PATH = os.path.join(static_dir, "gallery_ico.ico")
GALLERY_DEF_ICO_PATH = os.path.join(static_dir, "gallery_def_ico.ico")
GALLERY_EXT_ICO_PATH = os.path.join(static_dir, "gallery_ext_ico.ico")
APP_ICO_PATH = os.path.join(static_dir, "happypanda.ico")
STAR_BTN_PATH = os.path.join(static_dir, "btn_star.png")
STAR_PATH = os.path.join(static_dir, "star.png")
STAR_SMALL_PATH = os.path.join(static_dir, "star_small.png")
PLUS_PATH = os.path.join(static_dir, "plus.png")
HOME_BTN_PATH = os.path.join(static_dir, "home.png")
SETTINGS_PATH = os.path.join(static_dir, "settings.png")
GRID_PATH = os.path.join(static_dir, "grid.png")
LIST_PATH = os.path.join(static_dir, "list.png")
NO_IMAGE_PATH = os.path.join(static_dir, "default.jpg")
SEARCH_OPTIONS_PATH = os.path.join(static_dir, "search_options.png")
typicons_root = os.path.join(static_dir, "typicons")
GLIST_PATH = os.path.join(typicons_root, "media-stop-outline.svg")
GARTIST_PATH = os.path.join(typicons_root, "user-outline.svg")
GROUP_PATH = os.path.join(typicons_root, "group-outline.svg")
TAG_PATH = os.path.join(typicons_root, "tags.svg")

# Monitored Paths
OVERRIDE_MONITOR = False  # set true to make watchers to ignore next item (will be set to False)
LOOK_NEW_GALLERY_STARTUP = get(True, 'Application', 'look new gallery startup', bool)
ENABLE_MONITOR = get(True, 'Application', 'enable monitor', bool)
MONITOR_PATHS = [p for p in get([], 'Application', 'monitor paths', list) if os.path.exists(p)]
IGNORE_PATHS = get([], 'Application', 'ignore paths', list)
IGNORE_EXTS = get([], 'Application', 'ignore exts', list)
SCANNING_FOR_GALLERIES = False  # if a scan for new galleries is being done
TEMP_PATH_IGNORE = []

# GENERAL
# set to true to make a fetch instance ignore moving files (will be set to false)
OVERRIDE_MOVE_IMPORTED_IN_FETCH = False
MOVE_IMPORTED_GALLERIES = get(False, 'Application', 'move imported galleries', bool)
IMPORTED_GALLERY_DEF_PATH = get('', 'Application', 'imported gallery def path', str)
OPEN_RANDOM_GALLERY_CHAPTERS = get(False, 'Application', 'open random gallery chapters', bool)
# set to true to make a fetch instance treat subfolder as galleries (will be set to false)
OVERRIDE_SUBFOLDER_AS_GALLERY = False
SUBFOLDER_AS_GALLERY = get(False, 'Application', 'subfolder as gallery', bool)
RENAME_GALLERY_SOURCE = get(False, 'Application', 'rename gallery source', bool)
EXTRACT_CHAPTER_BEFORE_OPENING = get(True, 'Application', 'extract chapter before opening', bool)
OPEN_GALLERIES_SEQUENTIALLY = get(False, 'Application', 'open galleries sequentially', bool)
SEND_FILES_TO_TRASH = get(True, 'Application', 'send files to trash', bool)
SHOW_SIDEBAR_WIDGET = get(False, 'Application', 'show sidebar widget', bool)

# ADVANCED
GALLERY_DATA_FIX_REGEX = get("", 'Advanced', 'gallery data fix regex', str)
GALLERY_DATA_FIX_TITLE = get(True, 'Advanced', 'gallery data fix title', bool)
GALLERY_DATA_FIX_ARTIST = get(True, 'Advanced', 'gallery data fix artist', bool)
GALLERY_DATA_FIX_REPLACE = get("", 'Advanced', 'gallery data fix replace', str)

EXTERNAL_VIEWER_ARGS = get("{$file}", 'Advanced', 'external viewer args', str)

# Import/Export
EXPORT_FORMAT = get(1, 'Advanced', 'export format', int)
EXPORT_PATH = ''

# HASH
HASH_GALLERY_PAGES = get('all', 'Advanced', 'hash gallery pages', int, str)

# WEB
INCLUDE_EH_EXPUNGED = get(False, 'Web', 'include eh expunged', bool)
GLOBAL_EHEN_TIME = get(5, 'Web', 'global ehen time offset', int)
GLOBAL_EHEN_LOCK = False
DEFAULT_EHEN_URL = get('http://g.e-hentai.org/', 'Web', 'default ehen url', str)
REPLACE_METADATA = get(False, 'Web', 'replace metadata', bool)
ALWAYS_CHOOSE_FIRST_HIT = get(False, 'Web', 'always choose first hit', bool)
USE_GALLERY_LINK = get(True, 'Web', 'use gallery link', bool)
USE_JPN_TITLE = get(False, 'Web', 'use jpn title', bool)
CONTINUE_AUTO_METADATA_FETCHER = get(True, 'Web', 'continue auto metadata fetcher', bool)
HEN_DOWNLOAD_TYPE = get(0, 'Web', 'hen download type', int)
DOWNLOAD_DIRECTORY = get('downloads', 'Web', 'download directory', str)
TORRENT_CLIENT = get('', 'Web', 'torrent client', str)
HEN_LIST = get(['chaikahen'], 'Web', 'hen list', list)
DOWNLOAD_GALLERY_TO_LIB = get(False, 'Web', 'download galleries to library', bool)

# External Viewer
EXTERNAL_VIEWER_SUPPORT = {'honeyview': ['Honeyview.exe']}
USE_EXTERNAL_VIEWER = get(False, 'Application', 'use external viewer', bool)
EXTERNAL_VIEWER_PATH = os.path.normcase(get('', 'Application', 'external viewer path', str))
_REFRESH_EXTERNAL_VIEWER = False

# controls
THUMBNAIL_CACHE_SIZE = (1024, get(200, 'Advanced', 'cache size', int))  # 1024 is 1mib
# amount of items to prefetch
PREFETCH_ITEM_AMOUNT = get(50, 'Advanced', 'prefetch item amount', int)
# controls how many steps it takes when scrolling
SCROLL_SPEED = get(7, 'Advanced', 'scroll speed', int)

# POPUP
POPUP_WIDTH = get(500, 'Visual', 'popup.w', int)
POPUP_HEIGHT = get(300, 'Visual', 'popup.h', int)

# Gallery
KEEP_ADDED_GALLERIES = get(True, 'Application', 'keep added galleries', bool)
GALLERY_METAFILE_KEYWORDS = ('info.json', 'info.txt')
CURRENT_SORT = get('title', 'General', 'current sort')
HIGH_QUALITY_THUMBS = get(False, 'Visual', 'high quality thumbs', bool)
USE_EXTERNAL_PROG_ICO = get(
    False, 'Visual', 'use external prog ico', bool
) if not sys.platform.startswith('darwin') else False
DISPLAY_GALLERY_TYPE = get(
    False, 'Visual', 'display gallery type', bool
) if not sys.platform.startswith('darwin') else False
DISPLAY_GALLERY_RIBBON = get(True, 'Visual', 'display gallery ribbon', bool)
GALLERY_FONT = (get('Segoe UI', 'Visual', 'gallery font family', str),
                get(11, 'Visual', 'gallery font size', int))
GALLERY_FONT_ELIDE = get(True, 'Visual', 'gallery font elide', bool)

G_DEF_LANGUAGE = get('English', 'General', 'gallery default language', str)
G_CUSTOM_LANGUAGES = get([], 'General', 'gallery custom languages', list)
G_DEF_STATUS = get('Completed', 'General', 'gallery default status', str)
G_DEF_TYPE = get('Doujinshi', 'General', 'gallery default type', str)
G_LANGUAGES = ["English", "Japanese", "Chinese", "Other"]
G_STATUS = ["Ongoing", "Completed", "Unknown"]
G_TYPES = [
    "Manga", "Doujinshi", "Artist CG Sets", "Game CG Sets", "Western", "Image Sets",
    "Non-H", "Cosplay", "Other"]


@enum.unique
class GalleryState(enum.Enum):
    """gallery state."""

    Default = 1
    New = 2

# Colors
GRID_VIEW_TITLE_COLOR = get('#323232', 'Visual', 'grid view title color', str)
GRID_VIEW_ARTIST_COLOR = get('#585858', 'Visual', 'grid view artist color', str)
GRID_VIEW_LABEL_COLOR = get('#F2F2F2', 'Visual', 'grid view label color', str)

GRID_VIEW_T_MANGA_COLOR = get('#3498db', 'Visual', 'grid view t manga color', str)
GRID_VIEW_T_DOUJIN_COLOR = get('#e74c3c', 'Visual', 'grid view t doujin color', str)
GRID_VIEW_T_ARTIST_CG_COLOR = get('#16a085', 'Visual', 'grid view t artist cg color', str)
GRID_VIEW_T_GAME_CG_COLOR = get('#2ecc71', 'Visual', 'grid view t game cg color', str)
GRID_VIEW_T_WESTERN_COLOR = get('#ecf0f1', 'Visual', 'grid view t western color', str)
GRID_VIEW_T_IMAGE_COLOR = get('#f39c12', 'Visual', 'grid view t image color', str)
GRID_VIEW_T_NON_H_COLOR = get('#f1c40f', 'Visual', 'grid view t non-h color', str)
GRID_VIEW_T_COSPLAY_COLOR = get('#9b59b6', 'Visual', 'grid view t cosplay color', str)
GRID_VIEW_T_OTHER_COLOR = get('#34495e', 'Visual', 'grid view t other color', str)

# Search
SEARCH_AUTOCOMPLETE = get(True, 'Application', 'search autocomplete', bool)
GALLERY_SEARCH_REGEX = get(False, 'Application', 'allow search regex', bool)
SEARCH_ON_ENTER = get(False, 'Application', 'search on enter', bool)
GALLERY_SEARCH_STRICT = get(False, 'Application', 'gallery search strict', bool)
GALLERY_SEARCH_CASE = get(False, 'Application', 'gallery search case', bool)


@enum.unique
class Search(enum.Enum):
    """search."""

    Strict = 1
    Case = 2
    Regex = 3

# Grid Tooltip
GRID_TOOLTIP = get(True, 'Visual', 'grid tooltip', bool)
TOOLTIP_TITLE = get(False, 'Visual', 'tooltip title', bool)
TOOLTIP_AUTHOR = get(False, 'Visual', 'tooltip author', bool)
TOOLTIP_CHAPTERS = get(True, 'Visual', 'tooltip chapters', bool)
TOOLTIP_STATUS = get(True, 'Visual', 'tooltip status', bool)
TOOLTIP_TYPE = get(True, 'Visual', 'tooltip type', bool)
TOOLTIP_LANG = get(False, 'Visual', 'tooltip lang', bool)
TOOLTIP_DESCR = get(False, 'Visual', 'tooltip descr', bool)
TOOLTIP_TAGS = get(False, 'Visual', 'tooltip tags', bool)
TOOLTIP_LAST_READ = get(True, 'Visual', 'tooltip last read', bool)
TOOLTIP_TIMES_READ = get(True, 'Visual', 'tooltip times read', bool)
TOOLTIP_PUB_DATE = get(False, 'Visual', 'tooltip pub date', bool)
TOOLTIP_DATE_ADDED = get(True, 'Visual', 'tooltip date added', bool)

GALLERY_ADDITION_DATA = []
GALLERY_DATA = []  # contains the most up to date gallery data
GALLERY_LISTS = set()  # contains the most up to dat gallery lists


# Exceptions
class MetadataFetchFail(Exception):
    """metadata fetch fail."""

    pass


class InternalPagesMismatch(Exception):
    """internal pages mismatch."""

    pass


class ChapterExists(Exception):
    """chapter exists."""

    pass


class ChapterWrongParentGallery(Exception):
    """chapter wrong parent gallery."""

    pass


class CreateArchiveFail(Exception):
    """create archive fail."""

    pass


class FileNotFoundInArchive(Exception):
    """file not found in archive."""

    pass


class WrongURL(Exception):
    """wrong url."""

    pass


class NeedLogin(Exception):
    """need login."""

    pass


class WrongLogin(Exception):
    """wrong login."""

    pass

EXTERNAL_VIEWER_INFO =\
    """{$folder} = path to folder
{$file} = path to first image

Tip: IrfanView uses {$file}
    """

WHAT_IS_FILTER =\
    """Filters are basically predefined gallery search terms.
Every time a gallery matches the specific filter it gets automatically added to the list!

Filter works the same way a gallery search does so make sure to read the guide in
Settings -> About -> Search Guide.
You can write any valid gallery search term.

Enabling Enforce will only allow galleries matching the specified filter in the ist.
"""

SUPPORTED_DOWNLOAD_URLS =\
    """Supported URLs:
- exhentai/g.e-hentai gallery urls, e.g.: http://g.e-hentai.org/g/618395/0439fa3666/
- panda.chaika.moe gallery and archive urls
    http://panda.chaika.moe/[0]/[1]/ where [0] is 'gallery' or 'archive' and [1] is numbers
    """

SUPPORTED_METADATA_URLS =\
    """Supported gallery URLs:
- exhentai/g.e-hentai gallery urls, e.g.: http://g.e-hentai.org/g/618395/0439fa3666/
- panda.chaika.moe gallery and archive urls
    http://panda.chaika.moe/[0]/[1]/ where [0] is 'gallery' or 'archive' and [1] is numbers
    """

EXHEN_COOKIE_TUTORIAL =\
    """
How do you find these two values? <br \>
<b>Firefox/Chrome/Others</b> <br \>
1. Navigate to exhentai.org <br \>
2. Right click --> Inspect element <br \>
3. Go on 'Console' tab <br \>
4. Write : 'document.cookie' <br \>
5. A line of values should appear that correspond to active cookies <br \>
6. Look for the 'ipb_member_id' and 'ipb_pass_hash' values <br \>
"""

ABOUT = \
    """
<!DOCTYPE html><html><head></head><body>
<p><strong>Creator</strong>: <a href="https://github.com/Pewpews">Pewpews</a></p>
<p>Chat: <a href="https://gitter.im/Pewpews/happypanda">Gitter chat</a></p>
<p>Email: <code>happypandabugs@gmail.com</code></p>
<p><strong>Current version</strong>: {}</p>
<p><strong>Current database version</strong>: {}</p>
<p>License: <a href="https://www.gnu.org/licenses/gpl-2.0.txt">
GENERAL PUBLIC LICENSE, Version 2</a></p>
<p>Happypanda was created using:</p>
<ul>
<li>Python 3.4</li>
<li>The Qt5 Framework</li>
<li>Various python libraries (see github repo)</li>
</ul>
<p>Contributors (github):
nonamethanks, ImoutoChan, Moshidesu, peaceanpizza, utterbull, LePearlo</p>

</body></html>
    """ .format(vs, db_constants.CURRENT_DB_VERSION)

# use html file.
_html_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'res', 'html')
with open(os.path.join(_html_dir, 'regex_cheat.html')) as f:
    REGEXCHEAT = f.read()
with open(os.path.join(_html_dir, 'trouble_guide.html')) as f:
    TROUBLE_GUIDE = f.read()
with open(os.path.join(_html_dir, 'search_tutorial_tags.html')) as f:
    SEARCH_TUTORIAL_TAGS = f.read()
with open(os.path.join(_html_dir, 'keyboard_shotrcuts_info.html')) as f:
    KEYBOARD_SHORTCUTS_INFO = f.read()
