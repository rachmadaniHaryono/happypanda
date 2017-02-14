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
    from asm_manager import AsmManager
    from chaika_hen import ChaikaHen
    from chaika_manager import ChaikaManager
    from ehen import EHen
    from exhen_manager import ExHenManager
    from hen_manager import HenManager
    from nhen_manager import NhenManager
except ImportError:
    from . import (
        app_constants,
        settings,
    )
    from .asm_manager import AsmManager
    from .chaika_hen import ChaikaHen
    from .chaika_manager import ChaikaManager
    from .ehen import EHen
    from .exhen import ExHen
    from .exhen_manager import ExHenManager
    from .hen_manager import HenManager
    from .nhen_manager import NhenManager

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


def _get_exhen_manager():
    """get exhen manager."""
    exprops = settings.ExProperties()
    if exprops.check():
        return ExHenManager
    else:
        return


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

    exhen_validation = regex_validate("((exhentai)\.org\/g\/[0-9]+\/[a-z0-9]+)")
    manager_dict = {
        HenManager: regex_validate("((g\.e-hentai)\.org\/g\/[0-9]+\/[a-z0-9]+)"),
        ChaikaManager: regex_validate("(panda\.chaika\.moe\/(archive|gallery)\/[0-9]+)"),
        AsmManager: regex_validate("(asmhentai\.com\/g\/[0-9]+)"),
        NhenManager: regex_validate("(nhentai.net\/g\/[0-9]+)"),
        _get_exhen_manager: exhen_validation,
    }
    if any(manager_dict.values()):
        match_dict = [(k, v) for k, v in manager_dict.items() if v]
        match_manager = match_dict[0][0]
        if match_manager is None and exhen_validation:
            return
        manager = match_manager()
    else:
        raise app_constants.WrongURL

    return manager
