"""pewnet module."""
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

import logging
import re as regex

try:  # pragma: no cover
    import app_constants
    import settings
    from asmhen_manager import AsmManager
    from chaika_hen import ChaikaHen
    from chaika_manager import ChaikaManager
    from ehen import EHen
    from exhen_manager import ExHenManager
    from hen_manager import HenManager
except ImportError:
    from . import (
        app_constants,
        settings,
    )
    from .asmhen_manager import AsmManager
    from .chaika_hen import ChaikaHen
    from .chaika_manager import ChaikaManager
    from .ehen import EHen
    from .exhen import ExHen
    from .exhen_manager import ExHenManager
    from .hen_manager import HenManager

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

DOWNLOAD_TYPE_ARCHIVE = 0
DOWNLOAD_TYPE_TORRENT = 1
DOWNLOAD_TYPE_OTHER = 2


def hen_list_init():
    """hen list init."""
    h_list = []
    for h in app_constants.HEN_LIST:
        if h == "ehen":
            h_list.append(EHen)
        elif h == "exhen":
            h_list.append(ExHen)
        elif h == "chaikahen":
            h_list.append(ChaikaHen)
    return h_list


def website_validator(url):
    """validate website.

    Args:
        url(str):Url to validate.
    Returns:
        manager of the said url when valid.
    """
    match_prefix = "^(http\:\/\/|https\:\/\/)?(www\.)?([^\.]?)"  # http:// or https:// + www.
    # match_base = "(.*\.)+" # base. Replace with domain
    # match_tld = "[a-zA-Z0-9][a-zA-Z0-9\-]*" # com
    end = "/?$"

    # NOTE ATTENTION: the prefix will automatically get prepended to the pattern string!
    # Don't try to match it.

    def regex_validate(r):
        if regex.fullmatch(match_prefix + r + end, url):
            return True
        return False

    if regex_validate("((g\.e-hentai)\.org\/g\/[0-9]+\/[a-z0-9]+)"):
        manager = HenManager()
    elif regex_validate("((exhentai)\.org\/g\/[0-9]+\/[a-z0-9]+)"):
        exprops = settings.ExProperties()
        if exprops.check():
            manager = ExHenManager()
        else:
            return
    elif regex_validate("(panda\.chaika\.moe\/(archive|gallery)\/[0-9]+)"):
        manager = ChaikaManager()
    elif regex_validate("(asmhentai\.com\/g\/[0-9]+)"):
        manager = AsmManager()
    else:
        raise app_constants.WrongURL

    return manager
