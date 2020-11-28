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
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import logging
import zipfile
import hashlib
import shutil
import uuid
import re
import re as regex
from typing import ClassVar, Union, List, Dict, AnyStr, io, Optional, TYPE_CHECKING

import webbrowser
import scandir
import rarfile
import json
import send2trash
import functools
import time

from PyQt5.QtGui import QImage, qRgba
from PIL import Image, ImageChops

from . import app_constants
from .database import db_constants
if TYPE_CHECKING:
    from . import gallerydb

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

IMG_FILES = ('.jpg', '.bmp', '.png', '.gif', '.jpeg')
ARCHIVE_FILES = ('.zip', '.cbz', '.rar', '.cbr')
FILE_FILTER = '*.zip *.cbz *.rar *.cbr'
IMG_FILTER = '*.jpg *.bmp *.png *.jpeg'
rarfile.PATH_SEP = '/'
rarfile.UNRAR_TOOL = app_constants.unrar_tool_path
if not app_constants.unrar_tool_path:
    FILE_FILTER = '*.zip *.cbz'
    ARCHIVE_FILES = ('.zip', '.cbz')


class GMetafile:
    files: List[io.TextIO]

    def __init__(self, path=None, archive=''):
        self.metadata = {
            "title": '',
            "artist": '',
            "type": '',
            "tags": {},
            "language": '',
            "pub_date": '',
            "link": '',
            "info": '',

        }
        self.files = []
        if path is None:
            return
        if archive:
            f_zip = ArchiveFile(archive)
            c = f_zip.dir_contents(path)
            for x in c:
                if x.endswith(app_constants.GALLERY_METAFILE_KEYWORDS):
                    self.files.append(open(f_zip.extract(x), encoding='utf-8'))
        else:
            for p in scandir.scandir(path):
                if p.name in app_constants.GALLERY_METAFILE_KEYWORDS:
                    self.files.append(open(p.path, encoding='utf-8'))
        if self.files:
            self.detect()
        else:
            log_d('No metafile found...')

    def _eze(self, fp: io.TextIO):
        """
        2020-11-09: TODO: find what site metadata this is
        Possibly panda chaika moe metadata
        """
        if not fp.name.endswith('.json'):
            return
        j = json.load(fp, encoding='utf-8')
        eze = ['gallery_info', 'image_api_key', 'image_info']
        # eze
        if all(x in j for x in eze):
            log_i('Detected metafile: eze')
            ezedata = j['gallery_info']
            t_parser = title_parser(ezedata['title'])
            self.metadata['title'] = t_parser['title']
            self.metadata['type'] = ezedata['category']
            for ns in ezedata['tags']:
                self.metadata['tags'][ns.capitalize()] = ezedata['tags'][ns]
            self.metadata['tags']['default'] = self.metadata['tags'].pop('Misc', [])
            self.metadata['artist'] = self.metadata['tags']['Artist'][0].capitalize() \
                if 'Artist' in self.metadata['tags'] else t_parser['artist']
            self.metadata['language'] = ezedata['language']
            d = ezedata['upload_date']
            # should be zero padded
            d[1] = int("0" + str(d[1])) if len(str(d[1])) == 1 else d[1]
            d[3] = int("0" + str(d[1])) if len(str(d[1])) == 1 else d[1]
            self.metadata['pub_date'] = datetime.datetime.strptime("{} {} {}".format(d[0], d[1], d[3]), "%Y %m %d")
            l = ezedata['source']
            self.metadata['link'] = 'http://' + l['site'] + '.org/g/' + str(l['gid']) + '/' + l['token']
            return True

    def _hdoujindler(self, fp: io.TextIO):
        """HDoujin Downloader"""
        if fp.name.endswith('info.txt'):
            log_i('Detected metafile: HDoujin text')
            lines = fp.readlines()
            if lines:
                for line in lines:
                    splitted = line.split(':', 1)
                    if len(splitted) > 1:
                        other = splitted[1].strip()
                        if not other:
                            continue
                        l = splitted[0].lower()
                        if "title" == l:
                            self.metadata['title'] = other
                        if "artist" == l:
                            self.metadata['artist'] = other.capitalize()
                        if "tags" == l:
                            self.metadata['tags'].update(tag_to_dict(other))
                        if "description" == l:
                            self.metadata['info'] = other
                        if "circle" in l:
                            if not "group" in self.metadata['tags']:
                                self.metadata['tags']['group'] = []
                                self.metadata['tags']['group'].append(other.strip().lower())
                        if "url" == l:
                            self.metadata['link'] = other
                return True

        ## Doesnt work for some reason.. too lazy to debug
        # elif fp.name.endswith('info.json'):
        #    log_i('Detected metafile: HDoujin json')
        #    j = json.load(fp, encoding='utf-8')
        #    j = j['manga_info']
        #    self.metadata['title'] = j['title']
        #    for n, a in enumerate(j['artist']):
        #        at = a
        #        if not n+1 == len(j['artist']):
        #            at += ', '
        #        self.metadata['artist'] += at
        #        tags = {}
        #        for x in j['tags']:
        #            ns = 'default' if x == 'misc' else x.capitalize()
        #            tags[ns] = []
        #            for y in j[tags][x]:
        #                tags[ns].append(y.strip().lower())
        #        self.metadata['tags'] = tags
        #        self.metadata['link'] = j['url']
        #        self.metadata['info'] = j['description']
        #        for x in j['circle']:
        #            if not "group" in self.metadata['tags']:
        #                self.metadata['tags']['group'] = []
        #                self.metadata['tags']['group'].append(x.strip().lower())
        #        return True

    def detect(self):
        for fp in self.files:
            with fp:
                z = False
                for x in [self._eze, self._hdoujindler]:
                    try:
                        if x(fp):
                            z = True
                            break
                    except Exception:
                        log.exception('Error in parsing metafile')
                        continue
                if not z:
                    log_i('Incompatible metafiles found')

    def update(self, other):
        self.metadata.update((x, y) for x, y in other.metadata.items() if y)

    def set_gallery_attr(self, gallery: gallerydb.Gallery, metadata_key: str,
                         gallery_attr: Optional[str] = None) -> None:

        if not gallery_attr:
            gallery_attr = metadata_key

        if not hasattr(gallery, gallery_attr):
            raise ValueError(
                "Gallery object does not have an attribute '{}' for its value to be set with metadata key '{}'"
                .format(gallery_attr, metadata_key)
            )

        if metadata_key in self.metadata:
            val = self.metadata[metadata_key]
            if not val:
                log_d("No value for metadata key %s", metadata_key)
            else:
                setattr(gallery, gallery_attr, val)

    def apply_gallery(self, gallery: gallerydb.Gallery):
        log_i('Applying metafile to gallery')
        for attr in ['title', 'artist', 'type', 'tags', 'pub_date', 'link', 'info']:
            self.set_gallery_attr(gallery, attr)

        return gallery


def backup_database(db_path=db_constants.DB_PATH):
    log_i("Perfoming database backup")
    date = "{}".format(datetime.datetime.today()).split(' ')[0]
    base_path, name = os.path.split(db_path)
    backup_dir = os.path.join(base_path, 'backup')
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)
    db_name = "{}-{}".format(date, name)

    current_try = 0
    orig_db_name = db_name
    while current_try < 50:
        if current_try:
            db_name = "{}({})-{}".format(date, current_try, orig_db_name)
        try:
            dst_path = os.path.join(backup_dir, db_name)
            if os.path.exists(dst_path):
                raise ValueError
            shutil.copyfile(db_path, dst_path)
            break
        except ValueError:
            current_try += 1
    log_i("Database backup perfomed: {}".format(db_name))
    return True


def get_date_age(date):
    """
    Take a datetime and return its "age" as a string.
    The age can be in second, minute, hour, day, month or year. Only the
    biggest unit is considered, e.g. if it's 2 days and 3 hours, "2 days" will
    be returned.
    Make sure date is not in the future, or else it won't work.
    """

    def formatn(n, s):
        """Add "s" if it's plural"""

        if n == 1:
            return "1 %s" % s
        elif n > 1:
            return "%d %ss" % (n, s)

    def q_n_r(a, b):
        """Return quotient and remaining"""

        return a / b, a % b

    class PrettyDelta:
        def __init__(self, dt):
            now = datetime.datetime.now()

            delta = now - dt
            self.day = delta.days
            self.second = delta.seconds

            self.year, self.day = q_n_r(self.day, 365)
            self.month, self.day = q_n_r(self.day, 30)
            self.hour, self.second = q_n_r(self.second, 3600)
            self.minute, self.second = q_n_r(self.second, 60)

        def format(self):
            for period in ['year', 'month', 'day', 'hour', 'minute', 'second']:
                n = getattr(self, period)
                if n > 0.9:
                    return formatn(n, period)
            return "0 second"

    return PrettyDelta(date).format()


def all_opposite(*args):
    """Returns true if all items in iterable evaluae to false"""
    for iterable in args:
        for x in iterable:
            if x:
                return False
    return True


def update_gallery_path(new_path, gallery):
    """Updates a gallery's chapters path"""
    for chap in gallery.chapters:
        head, tail = os.path.split(chap.path)
        if gallery.path == chap.path:
            chap.path = new_path
        elif gallery.path == head:
            chap.path = os.path.join(new_path, tail)

    gallery.path = new_path
    return gallery


def move_files(path, dest='', only_path=False):
    """
    Move files to a new destination. If dest is not set,
    imported_galleries_def_path will be used instead.
    """
    if not dest:
        dest = app_constants.IMPORTED_GALLERY_DEF_PATH
        if not dest:
            return path
    f = os.path.split(path)[1]
    new_path = os.path.join(dest, f)
    if not only_path:
        log_i("Moving to: {}".format(new_path))
    if new_path == os.path.join(*os.path.split(path)):  # need to unpack to make sure we get the corrct sep
        return path
    if not os.path.exists(new_path):
        app_constants.TEMP_PATH_IGNORE.append(os.path.normcase(new_path))
        if not only_path:
            new_path = shutil.move(path, new_path)
    else:
        return path
    return new_path


def check_ignore_list(key):
    k = os.path.normcase(key)
    if os.path.isdir(key) and 'Folder' in app_constants.IGNORE_EXTS:
        return False
    _, ext = os.path.splitext(key)
    if ext in app_constants.IGNORE_EXTS:
        return False
    for path in app_constants.IGNORE_PATHS:
        p = os.path.normcase(path)
        if p in k:
            return False
    return True


def gallery_text_fixer(gallery):
    regex_str = app_constants.GALLERY_DATA_FIX_REGEX
    if regex_str:
        try:
            valid_regex = re.compile(regex_str)
        except re.error:
            return None
        if not valid_regex:
            return None

        def replace_regex(text):
            new_text = re.sub(regex_str, app_constants.GALLERY_DATA_FIX_REPLACE, text)
            return new_text

        if app_constants.GALLERY_DATA_FIX_TITLE:
            gallery.title = replace_regex(gallery.title)
        if app_constants.GALLERY_DATA_FIX_ARTIST:
            gallery.artist = replace_regex(gallery.artist)

        return gallery


def b_search(data, key):
    if key:
        lo = 0
        hi = len(data) - 1
        while hi >= lo:
            mid = lo + (hi - lo) // 2
            if data[mid] < key:
                lo = mid + 1
            elif data[mid] > key:
                hi = mid - 1
            else:
                return data[mid]
    return None


def generate_img_hash(src):
    """
    Generates sha1 hash based on the given bytes.
    Returns hex-digits
    """
    chunk = 8129
    sha1 = hashlib.sha1()
    buffer = src.read(chunk)
    log_d("Generating hash")
    while len(buffer) > 0:
        sha1.update(buffer)
        buffer = src.read(chunk)
    return sha1.hexdigest()


class ArchiveFile:
    """
    Work with archive files, raises exception if instance fails.
    namelist -> returns a list with all files in archive
    extract <- Extracts one specific file to given path
    open -> open the given file in archive, returns bytes
    close -> close archive
    """
    zip: ClassVar[int] = 0
    rar: ClassVar[int] = 1

    type: int
    archive: Union[zipfile.ZipFile, rarfile.RarFile]

    def __init__(self, filepath: Union[str, 'os.PathLike']) -> None:
        self.type = 0
        try:
            if filepath.endswith(ARCHIVE_FILES):
                b_f = None
                if filepath.endswith(ARCHIVE_FILES[:2]):
                    self.archive = zipfile.ZipFile(os.path.normcase(filepath))
                    b_f = self.archive.testzip()
                    self.type = self.zip
                elif filepath.endswith(ARCHIVE_FILES[2:]):
                    self.archive = rarfile.RarFile(os.path.normcase(filepath))
                    b_f = self.archive.testrar()
                    self.type = self.rar

                # test for corruption
                if b_f:
                    log_w('Bad file found in archive {}'.format(filepath.encode(errors='ignore')))
                    raise app_constants.CreateArchiveFail
            else:
                log_e('Archive: Unsupported file format')
                raise app_constants.CreateArchiveFail
        except:
            log.exception('Create archive: FAIL')
            raise app_constants.CreateArchiveFail

    def namelist(self) -> List[str]:
        filelist = self.archive.namelist()
        return filelist

    def is_dir(self, name: str) -> bool:
        """
        Checks if the provided name in the archive is a directory or not
        """
        if not name:
            return False
        if name not in self.namelist():
            log_e('File {} not found in archive'.format(name))
            raise app_constants.FileNotFoundInArchive
        if self.type == self.zip:
            if name.endswith('/'):
                return True
        elif self.type == self.rar:
            info = self.archive.getinfo(name)
            return info.isdir()
        return False

    def dir_list(self, only_top_level=False) -> List[Union[str, 'os.PathLike']]:
        """
        Returns a list of all directories found recursively. For directories not in toplevel
        a path in the archive to the diretory will be returned.
        """

        if only_top_level:
            if self.type == self.zip:
                return [x for x in self.namelist() if x.endswith('/') and x.count('/') == 1]
            elif self.type == self.rar:
                potential_dirs = [x for x in self.namelist() if x.count('/') == 0]
                return [x.filename for x in [self.archive.getinfo(y) for y in potential_dirs] if x.isdir()]
        else:
            if self.type == self.zip:
                return [x for x in self.namelist() if x.endswith('/') and x.count('/') >= 1]
            elif self.type == self.rar:
                return [x.filename for x in self.archive.infolist() if x.isdir()]

    def dir_contents(self, dir_name: str) -> List:
        """
        Returns a list of contents in the directory
        An empty string will return the contents of the top folder
        """
        if dir_name and not dir_name in self.namelist():
            log_e('Directory {} not found in archive'.format(dir_name))
            raise app_constants.FileNotFoundInArchive
        if not dir_name:
            con = []
            if self.type == self.zip:
                con = [x for x in self.namelist() if x.count('/') == 0
                       or (x.count('/') == 1 and x.endswith('/'))]
            elif self.type == self.rar:
                con = [x for x in self.namelist() if x.count('/') == 0]
            return con
        if self.type == self.zip:
            dir_con_start = [x for x in self.namelist() if x.startswith(dir_name)]
            return [x for x in dir_con_start if x.count('/') == dir_name.count('/')
                    and (x.count('/') == dir_name.count('/') and not x.endswith('/'))
                    or (x.count('/') == 1 + dir_name.count('/') and x.endswith('/'))]
        elif self.type == self.rar:
            return [x for x in self.namelist() if x.startswith(dir_name)
                    and x.count('/') == 1 + dir_name.count('/')]
        return []

    def extract(self, file_to_ext, path=None) -> Union[str, 'os.PathLike']:
        """
        Extracts one file from archive to given path
        Creates a temp_dir if path is not specified
        Returns path to the extracted file
        """
        if not path:
            path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
            os.mkdir(path)

        if not file_to_ext:
            return self.extract_all(path)
        else:
            temp_p = ''
            if self.type == self.zip:
                membs = []
                for name in self.namelist():
                    if name.startswith(file_to_ext) and name != file_to_ext:
                        membs.append(name)
                temp_p = self.archive.extract(file_to_ext, path)
                for m in membs:
                    self.archive.extract(m, path)
            elif self.type == self.rar:
                temp_p = os.path.join(path, file_to_ext)
                self.archive.extract(file_to_ext, path)
            return temp_p

    def extract_all(self, path=None, member=None):
        """
        Extracts all files to given path, and returns path
        If path is not specified, a temp dir will be created
        """
        if not path:
            path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
            os.mkdir(path)
        if member:
            self.archive.extractall(path, member)
        self.archive.extractall(path)
        return path

    def open(self, file_to_open: str, fp=False) -> Union['AnyStr', 'io.IO[bytes]']:
        """
        Returns bytes. If fp set to true, returns file-like object.
        """
        if fp:
            return self.archive.open(file_to_open)
        else:
            return self.archive.open(file_to_open).read()

    def close(self) -> None:
        self.archive.close()


def check_archive(archive_path):
    """
    Checks archive path for potential galleries.
    Returns a list with a path in archive to galleries
    if there is no directories
    """
    try:
        f_zip = ArchiveFile(archive_path)
    except app_constants.CreateArchiveFail:
        return []
    if not f_zip:
        return []
    galleries = []
    zip_dirs = f_zip.dir_list()

    def gallery_eval(d):
        con = f_zip.dir_contents(d)
        if con:
            gallery_probability = len(con)
            for n in con:
                if not n.lower().endswith(IMG_FILES):
                    gallery_probability -= 1
            if gallery_probability >= (len(con) * 0.8):
                return d

    if zip_dirs:  # There are directories in the top folder
        # check parent
        r = gallery_eval('')
        if r:
            galleries.append('')
        for d in zip_dirs:
            r = gallery_eval(d)
            if r:
                galleries.append(r)
        f_zip.close()
    else:  # all pages are in top folder
        if isinstance(gallery_eval(''), str):
            galleries.append('')
        f_zip.close()

    return galleries


def recursive_gallery_check(path):
    """
    Recursively checks a folder for any potential galleries
    Returns a list of paths for directories and a list of tuples where first
    index is path to gallery in archive and second index is path to archive.
    Like this:
    ["C:path/to/g"] and [("path/to/g/in/a", "C:path/to/a")]
    """
    gallery_dirs = []
    gallery_arch = []
    found_paths = 0
    for root, subfolders, files in scandir.walk(path):
        if files:
            for f in files:
                if f.endswith(ARCHIVE_FILES):
                    arch_path = os.path.join(root, f)
                    for g in check_archive(arch_path):
                        found_paths += 1
                        gallery_arch.append((g, arch_path))

            if not subfolders:
                if not files:
                    continue
                gallery_probability = len(files)
                for f in files:
                    if not f.lower().endswith(IMG_FILES):
                        gallery_probability -= 1
                if gallery_probability >= (len(files) * 0.8):
                    found_paths += 1
                    gallery_dirs.append(root)
    log_i('Found {} in {}'.format(found_paths, path).encode(errors='ignore'))
    return gallery_dirs, gallery_arch


def today():
    """Returns current date in a list: [dd, Mmm, yyyy]"""
    _date = datetime.date.today()
    day = _date.strftime("%d")
    month = _date.strftime("%b")
    year = _date.strftime("%Y")
    return [day, month, year]


def external_viewer_checker(path):
    check_dict = app_constants.EXTERNAL_VIEWER_SUPPORT
    viewer = os.path.split(path)[1]
    for x in check_dict:
        allow = False
        for n in check_dict[x]:
            if viewer.lower() in n.lower():
                allow = True
                break
        if allow:
            return x


def open_chapter(chapterpath, archive=None):
    is_archive = True if archive else False
    if not is_archive:
        chapterpath = os.path.normpath(chapterpath)
    temp_p = archive if is_archive else chapterpath

    custom_args = app_constants.EXTERNAL_VIEWER_ARGS
    send_folder_t = '{$folder}'
    send_image_t = '{$file}'

    send_folder = True

    if app_constants.USE_EXTERNAL_VIEWER:
        send_folder = True

    if custom_args:
        if send_folder_t in custom_args:
            send_folder = True
        elif send_image_t in custom_args:
            send_folder = False

    def find_f_img_folder() -> Union[str, 'os.PathLike']:
        filepath = os.path.join(temp_p, [x for x in sorted([y.name for y in scandir.scandir(temp_p)]) \
                                         if x.lower().endswith(IMG_FILES) and not x.startswith('.')][
            0])  # Find first page
        return temp_p if send_folder else filepath

    def find_f_img_archive(extract=True) -> Union[str, 'os.PathLike']:
        f_zip = ArchiveFile(temp_p)
        if extract:
            app_constants.NOTIF_BAR.add_text('Extracting...')
            t_p = os.path.join('temp', str(uuid.uuid4()))
            os.mkdir(t_p)
            if is_archive or chapterpath.endswith(ARCHIVE_FILES):
                if os.path.isdir(chapterpath):
                    t_p = chapterpath
                elif chapterpath.endswith(ARCHIVE_FILES):
                    zip2 = ArchiveFile(chapterpath)
                    f_d = sorted(zip2.dir_list(True))
                    if f_d:
                        f_d = f_d[0]
                        t_p = zip2.extract(f_d, t_p)
                    else:
                        t_p = zip2.extract('', t_p)
                else:
                    t_p = f_zip.extract(chapterpath, t_p)
            else:
                f_zip.extract_all(t_p)  # Compatibility reasons..  TODO: REMOVE IN BETA
            if send_folder:
                fp = t_p
            else:
                fp = os.path.join(t_p, [x for x in sorted([y.name for y in scandir.scandir(t_p)]) \
                                        if x.lower().endswith(IMG_FILES) and not x.startswith('.')][
                    0])  # Find first page
                fp = os.path.abspath(fp)
        else:
            if is_archive or chapterpath.endswith(ARCHIVE_FILES):
                con = f_zip.dir_contents('')
                f_img = [x for x in sorted(con) if x.lower().endswith(IMG_FILES) and not x.startswith('.')]
                if not f_img:
                    log_w('Extracting archive.. There are no images in the top-folder. ({})'.format(archive))
                    return find_f_img_archive()
                fp = os.path.normpath(archive)
            else:
                app_constants.NOTIF_BAR.add_text("Fatal error: Unsupported gallery!")
                raise ValueError("Unsupported gallery version")
        return fp

    try:
        try:  # folder
            filepath = find_f_img_folder()
        except NotADirectoryError:  # archive
            try:
                if not app_constants.EXTRACT_CHAPTER_BEFORE_OPENING and app_constants.EXTERNAL_VIEWER_PATH:
                    filepath = find_f_img_archive(False)
                else:
                    filepath = find_f_img_archive()
            except app_constants.CreateArchiveFail:
                log.exception('Could not open chapter')
                app_constants.NOTIF_BAR.add_text('Could not open chapter. Check happypanda.log for more details.')
                return
    except FileNotFoundError:
        log.exception('Could not find chapter {}'.format(chapterpath))
        app_constants.NOTIF_BAR.add_text("Chapter does no longer exist!")
        return
    except IndexError:
        log.exception('No images found: {}'.format(chapterpath))
        app_constants.NOTIF_BAR.add_text("No images found in chapter!")
        return

    if send_folder_t in custom_args:
        custom_args = custom_args.replace(send_folder_t, filepath)
    elif send_image_t in custom_args:
        custom_args = custom_args.replace(send_image_t, filepath)
    else:
        custom_args = filepath

    try:
        app_constants.NOTIF_BAR.add_text('Opening chapter...')
        if not app_constants.USE_EXTERNAL_VIEWER:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', custom_args))
            elif os.name == 'nt':
                os.startfile(custom_args)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', custom_args))
        else:
            ext_path = app_constants.EXTERNAL_VIEWER_PATH
            viewer = external_viewer_checker(ext_path)
            if viewer == 'honeyview':
                if app_constants.OPEN_GALLERIES_SEQUENTIALLY:
                    subprocess.call((ext_path, custom_args))
                else:
                    subprocess.Popen((ext_path, custom_args))
            else:
                if app_constants.OPEN_GALLERIES_SEQUENTIALLY:
                    subprocess.check_call((ext_path, custom_args))
                else:
                    subprocess.Popen((ext_path, custom_args))
    except subprocess.CalledProcessError:
        app_constants.NOTIF_BAR.add_text("Could not open chapter. Invalid external viewer.")
        log.exception('Could not open chapter. Invalid external viewer.')
    except:
        app_constants.NOTIF_BAR.add_text("Could not open chapter for unknown reasons. Check happypanda.log!")
        log_e('Could not open chapter {}'.format(os.path.split(chapterpath)[1]))


def get_gallery_img(gallery_or_path: Union[gallerydb.Gallery, str, 'os.PathLike'], chap_number: int = 0) \
        -> Union[str, 'os.PathLike', None]:
    """
    Returns a path to image in gallery chapter
    """
    archive = None
    if isinstance(gallery_or_path, str):
        path = gallery_or_path
    else:
        path = gallery_or_path.chapters[chap_number].path
        if gallery_or_path.is_archive:
            archive = gallery_or_path.path

    # TODO: add chapter support
    try:
        name = os.path.split(path)[1]
    except IndexError:
        name = os.path.split(path)[0]
    is_archive = True if archive or name.endswith(ARCHIVE_FILES) else False
    real_path = archive if archive else path
    img_path: Union[str, 'os.PathLike', None] = None
    if is_archive:
        try:
            log_i('Getting image from archive')
            zip = ArchiveFile(real_path)
            temp_path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
            os.mkdir(temp_path)
            if not archive:
                f_img_name = \
                    sorted(
                        [img for img in zip.namelist() if img.lower().endswith(IMG_FILES) and not img.startswith('.')])[
                        0]
            else:
                f_img_name = sorted([img for img in zip.dir_contents(path) if
                                     img.lower().endswith(IMG_FILES) and not img.startswith('.')])[0]
            img_path = zip.extract(f_img_name, temp_path)
            zip.close()
        except app_constants.CreateArchiveFail:
            img_path = app_constants.NO_IMAGE_PATH
    elif os.path.isdir(real_path):
        log_i('Getting image from folder')
        first_img = sorted([img.name for img in scandir.scandir(real_path) if
                            img.name.lower().endswith(tuple(IMG_FILES)) and not img.name.startswith('.')])
        if first_img:
            img_path = os.path.join(real_path, first_img[0])

    if img_path:
        return os.path.abspath(img_path)
    else:
        log_e("Could not get gallery image")
        return None


def tag_to_string(gallery_tag: Dict, simple: bool = False) -> str:
    """
    Takes gallery tags and converts it to string, returns string
    if simple is set to True, returns a CSV string, else a dict-like string
    """
    assert isinstance(gallery_tag, dict), "Please provide a dict like this: {'namespace':['tag1']}"
    string = ""
    if not simple:
        for n, namespace in enumerate(sorted(gallery_tag), 1):
            if len(gallery_tag[namespace]) != 0:
                if namespace != 'default':
                    string += namespace + ":"

                # find tags
                if namespace != 'default' and len(gallery_tag[namespace]) > 1:
                    string += '['
                for x, tag in enumerate(sorted(gallery_tag[namespace]), 1):
                    # if we are at the end of the list
                    if x == len(gallery_tag[namespace]):
                        string += tag
                    else:
                        string += tag + ', '
                if namespace != 'default' and len(gallery_tag[namespace]) > 1:
                    string += ']'

                # if we aren't at the end of the list
                if not n == len(gallery_tag):
                    string += ', '
    else:
        for n, namespace in enumerate(sorted(gallery_tag), 1):
            if len(gallery_tag[namespace]) != 0:
                if namespace != 'default':
                    string += namespace + ","

                # find tags
                for x, tag in enumerate(sorted(gallery_tag[namespace]), 1):
                    # if we are at the end of the list
                    if x == len(gallery_tag[namespace]):
                        string += tag
                    else:
                        string += tag + ', '

                # if we aren't at the end of the list
                if not n == len(gallery_tag):
                    string += ', '

    return string


def tag_to_dict(string: str, ns_capitalize=True) -> Dict:
    """Receives a string of tags and converts it to a dict of tags"""
    namespace_tags = {'default': []}
    level = 0  # so we know if we are in a list
    buffer = ""
    stripped_set = set()  # we only need unique values
    for n, x in enumerate(string, 1):

        if x == '[':
            level += 1  # we are now entering a list
        if x == ']':
            level -= 1  # we are now exiting a list

        if x == ',':  # if we meet a comma
            # we trim our buffer if we are at top level
            if level == 0:
                # add to list
                stripped_set.add(buffer.strip())
                buffer = ""
            else:
                buffer += x
        elif n == len(string):  # or at end of string
            buffer += x
            # add to list
            stripped_set.add(buffer.strip())
            buffer = ""
        else:
            buffer += x

    def tags_in_list(br_tags):
        """Receives a string of tags enclosed in brackets, returns a list with tags"""
        unique_tags = set()
        tags = br_tags.replace('[', '').replace(']', '')
        tags = tags.split(',')
        for t in tags:
            if len(t) != 0:
                unique_tags.add(t.strip().lower())
        return list(unique_tags)

    unique_tags = set()
    for ns_tag in stripped_set:
        splitted_tag = ns_tag.split(':')
        # if there is a namespace
        if len(splitted_tag) > 1 and len(splitted_tag[0]) != 0:
            if splitted_tag[0] != 'default':
                if ns_capitalize:
                    namespace = splitted_tag[0].capitalize()
                else:
                    namespace = splitted_tag[0]
            else:
                namespace = splitted_tag[0]
            tags = splitted_tag[1]
            # if tags are enclosed in brackets
            if '[' in tags and ']' in tags:
                tags = tags_in_list(tags)
                tags = [x for x in tags if len(x) != 0]
                # if namespace is already in our list
                if namespace in namespace_tags:
                    for t in tags:
                        # if tag not already in ns list
                        if not t in namespace_tags[namespace]:
                            namespace_tags[namespace].append(t)
                else:
                    # to avoid empty strings
                    namespace_tags[namespace] = tags
            else:  # only one tag
                if len(tags) != 0:
                    if namespace in namespace_tags:
                        namespace_tags[namespace].append(tags)
                    else:
                        namespace_tags[namespace] = [tags]
        else:  # no namespace specified
            tag = splitted_tag[0]
            if len(tag) != 0:
                unique_tags.add(tag.lower())

    if len(unique_tags) != 0:
        for t in unique_tags:
            namespace_tags['default'].append(t)

    return namespace_tags


def title_parser(title):
    """Receives a title to parse. Returns dict with 'title', 'artist' and language"""
    log_d("Parsing title: {}".format(title))

    #If title is not absolute, then it's not a pathname and we allow a "/" inside it
    if(os.path.isabs(title)):
        title = os.path.basename(title)
    title = " ".join(title.split())
    # if '/' in title:
    #     try:
    #         title = os.path.split(title)[1]
    #         if not title:
    #             title = title
    #     except IndexError:
    #         pass

    for x in ARCHIVE_FILES:
        if title.endswith(x):
            title = title[:-len(x)]

    parsed_title = {'title': "", 'artist': "", 'language': ""}
    try:
        a = regex.findall(r'((?<=\[) *[^\]]+( +\S+)* *(?=\]))', title)
        assert len(a) != 0
        try:
            artist = a[0][0].strip()
        except IndexError:
            artist = ''
        parsed_title['artist'] = artist

        try:
            assert a[1]
            lang = app_constants.G_LANGUAGES + app_constants.G_CUSTOM_LANGUAGES
            for x in a:
                l = x[0].strip()
                l = l.lower()
                l = l.capitalize()
                if l in lang:
                    parsed_title['language'] = l
                    break
            else:
                parsed_title['language'] = app_constants.G_DEF_LANGUAGE
        except IndexError:
            parsed_title['language'] = app_constants.G_DEF_LANGUAGE

        t = title
        for x in a:
            t = t.replace(x[0], '')

        t = t.replace('[]', '')
        final_title = t.strip()
        parsed_title['title'] = final_title
    except AssertionError:
        parsed_title['title'] = title

    return parsed_title


def open_web_link(url) -> None:
    if not url:
        return
    try:
        webbrowser.open_new_tab(url)
    except:
        log_e('Could not open URL in browser')


def open_path(path, select=''):
    """"""
    try:
        if sys.platform.startswith('darwin'):
            subprocess.Popen(['open', path])
        elif os.name == 'nt':
            if select:
                subprocess.Popen(r'explorer.exe /select,"{}"'.format(os.path.normcase(select)), shell=True)
            else:
                os.startfile(path)
        elif os.name == 'posix':
            subprocess.Popen(('xdg-open', path))
        else:
            app_constants.NOTIF_BAR.add_text(
                "I don't know how you've managed to do this.. If you see this, you're in deep trouble...")
            log_e('Could not open path: no OS found')
    except:
        app_constants.NOTIF_BAR.add_text("Could not open specified location. It might not exist anymore.")
        log_e('Could not open path')


def open_torrent(path):
    if not app_constants.TORRENT_CLIENT:
        open_path(path)
    else:
        subprocess.Popen([app_constants.TORRENT_CLIENT, path])


def delete_path(path):
    """Deletes the provided recursively"""
    s = True
    if os.path.exists(path):
        error = ''
        if app_constants.SEND_FILES_TO_TRASH:
            try:
                send2trash.send2trash(path)
            except:
                log.exception("Unable to send file to trash")
                error = 'Unable to send file to trash'
        else:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except PermissionError:
                error = 'PermissionError'
            except FileNotFoundError:
                pass

        if error:
            p = os.path.split(path)[1]
            log_e('Failed to delete: {}:{}'.format(error, p))
            app_constants.NOTIF_BAR.add_text('An error occured while trying to delete: {}'.format(error))
            s = False
    return s


def regex_search(a, b, override_case=False, args: List = None):
    """Looks for a in b"""
    if args is None:
        args = []
    if a and b:
        try:
            if app_constants.Search.Case not in args or override_case:
                if regex.search(a, b, regex.IGNORECASE):
                    return True
            else:
                if regex.search(a, b):
                    return True
        except regex.error:
            pass
    return False


def search_term(a, b, override_case=False, args: Optional[List] = None):
    """Searches for a in b"""
    if args is None:
        args = []
    if a and b:
        if override_case or app_constants.Search.Case not in args:
            b = b.lower()
            a = a.lower()

        if app_constants.Search.Strict in args:
            if a == b:
                return True
        else:
            if a in b:
                return True
    return False


def get_terms(term):
    """Dividies term into pieces. Returns a list with the pieces"""

    # some variables we will use
    pieces = []
    piece = ''
    qoute_level = 0
    bracket_level = 0
    brackets_tags = {}
    current_bracket_ns = ''
    end_of_bracket = False
    blacklist = ['[', ']', '"', ',']

    for n, x in enumerate(term):
        # if we meet brackets
        if x == '[':
            bracket_level += 1
            brackets_tags[piece] = set()  # we want unique tags!
            current_bracket_ns = piece
        elif x == ']':
            bracket_level -= 1
            end_of_bracket = True

        # if we meet a double qoute
        if x == '"':
            if qoute_level > 0:
                qoute_level -= 1
            else:
                qoute_level += 1

        # if we meet a whitespace, comma or end of term and are not in a double qoute
        if (x == ' ' or x == ',' or n == len(term) - 1) and qoute_level == 0:
            # if end of term and x is allowed
            if (n == len(term) - 1) and not x in blacklist and x != ' ':
                piece += x
            if piece:
                if bracket_level > 0 or end_of_bracket:  # if we are inside a bracket we put piece in the set
                    end_of_bracket = False
                    if piece.startswith(current_bracket_ns):
                        piece = piece[len(current_bracket_ns):]
                    if piece:
                        try:
                            brackets_tags[current_bracket_ns].add(piece)
                        except KeyError:  # keyerror when there is a closing bracket without a starting bracket
                            pass
                else:
                    pieces.append(piece)  # else put it in the normal list
            piece = ''
            continue

        # else append to the buffers
        if not x in blacklist:
            if qoute_level > 0:  # we want to include everything if in double qoute
                piece += x
            elif x != ' ':
                piece += x

    # now for the bracket tags
    for ns in brackets_tags:
        for tag in brackets_tags[ns]:
            ns_tag = ns
            # if they want to exlucde this tag
            if tag[0] == '-':
                if ns_tag[0] != '-':
                    ns_tag = '-' + ns
                tag = tag[1:]  # remove the '-'

            # put them together
            ns_tag += tag

            # done
            pieces.append(ns_tag)

    return pieces


def image_greyscale(filepath):
    """
    Check if image is monochrome (1 channel or 3 identical channels)
    """
    log_d("Checking if img is monochrome: {}".format(filepath))
    im = Image.open(filepath).convert("RGB")
    if im.mode not in ("L", "RGB"):
        return False

    if im.mode == "RGB":
        rgb = im.split()
        if ImageChops.difference(rgb[0], rgb[1]).getextrema()[1] != 0:
            return False
        if ImageChops.difference(rgb[0], rgb[2]).getextrema()[1] != 0:
            return False
    return True


def PToQImageHelper(im):
    """
    The Python Imaging Library (PIL) is

    Copyright © 1997-2011 by Secret Labs AB
    Copyright © 1995-2011 by Fredrik Lundh
    """

    def rgb(r, g, b, a=255):
        """(Internal) Turns an RGB color into a Qt compatible color integer."""
        # use qRgb to pack the colors, and then turn the resulting long
        # into a negative integer with the same bitpattern.
        return qRgba(r, g, b, a) & 0xffffffff

    def align8to32(bytes, width, mode):
        """
        converts each scanline of data from 8 bit to 32 bit aligned
        """

        bits_per_pixel = {
            '1': 1,
            'L': 8,
            'P': 8,
        }[mode]

        # calculate bytes per line and the extra padding if needed
        bits_per_line = bits_per_pixel * width
        full_bytes_per_line, remaining_bits_per_line = divmod(bits_per_line, 8)
        bytes_per_line = full_bytes_per_line + (1 if remaining_bits_per_line else 0)

        extra_padding = -bytes_per_line % 4

        # already 32 bit aligned by luck
        if not extra_padding:
            return bytes

        new_data = []
        for i in range(len(bytes) // bytes_per_line):
            new_data.append(bytes[i * bytes_per_line:(i + 1) * bytes_per_line] + b'\x00' * extra_padding)

        return b''.join(new_data)

    data = None
    colortable = None

    # handle filename, if given instead of image name
    if hasattr(im, "toUtf8"):
        # FIXME - is this really the best way to do this?
        if str is bytes:
            im = im.toUtf8().decode('utf-8')
        else:
            im = str(im.toUtf8(), "utf-8")
    if isinstance(im, (bytes, str)):
        im = Image.open(im)

    if im.mode == "1":
        img_format = QImage.Format_Mono
    elif im.mode == "L":
        img_format = QImage.Format_Indexed8
        colortable = []
        for i in range(256):
            colortable.append(rgb(i, i, i))
    elif im.mode == "P":
        img_format = QImage.Format_Indexed8
        colortable = []
        palette = im.getpalette()
        for i in range(0, len(palette), 3):
            colortable.append(rgb(*palette[i:i + 3]))
    elif im.mode == "RGB":
        data = im.tobytes("raw", "BGRX")
        img_format = QImage.Format_RGB32
    elif im.mode == "RGBA":
        try:
            data = im.tobytes("raw", "BGRA")
        except SystemError:
            # workaround for earlier versions
            r, g, b, a = im.split()
            im = Image.merge("RGBA", (b, g, r, a))
        img_format = QImage.Format_ARGB32
    else:
        raise ValueError("unsupported image mode %r" % im.mode)

    # must keep a reference, or Qt will crash!
    __data = data or align8to32(im.tobytes(), im.size[0], im.mode)
    return {
        'data': __data, 'im': im, 'format': img_format, 'colortable': colortable
    }


def make_chapters(gallery_object):
    chap_container = gallery_object.chapters
    path = gallery_object.path
    metafile = GMetafile()
    try:
        log_d('Listing dir...')
        con = scandir.scandir(path)  # list all folders in gallery dir
        log_i('Gallery source is a directory')
        log_d('Sorting')
        chapters = sorted([sub.path for sub in con if sub.is_dir() or sub.name.endswith(ARCHIVE_FILES)])  # subfolders
        # if gallery has chapters divided into sub folders
        if len(chapters) != 0:
            log_d('Chapters divided in folders..')
            for ch in chapters:
                chap = chap_container.create_chapter()
                chap.title = title_parser(ch)['title']
                chap.path = os.path.join(path, ch)
                metafile.update(GMetafile(chap.path))
                chap.pages = len([x for x in scandir.scandir(chap.path) if x.name.lower().endswith(IMG_FILES)])

        else:  # else assume that all images are in gallery folder
            chap = chap_container.create_chapter()
            chap.title = title_parser(os.path.split(path)[1])['title']
            chap.path = path
            metafile.update(GMetafile(path))
            chap.pages = len([x for x in scandir.scandir(path) if x.name.lower().endswith(IMG_FILES)])

    except NotADirectoryError:
        if path.endswith(ARCHIVE_FILES):
            gallery_object.is_archive = 1
            log_i("Gallery source is an archive")
            archive_g = sorted(check_archive(path))
            for g in archive_g:
                chap = chap_container.create_chapter()
                chap.path = g
                chap.in_archive = 1
                metafile.update(GMetafile(g, path))
                arch = ArchiveFile(path)
                chap.pages = len(arch.dir_contents(g))
                arch.close()

    metafile.apply_gallery(gallery_object)


def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsed_time * 1000)))

    return newfunc


def makedirs_if_not_exists(folder):
    """Create directory if not exists.
    Args:
        folder: Target folder.
    """
    if not os.path.isdir(folder):
        os.makedirs(folder)


def lookup_tag(tag: str) -> None:
    """Issues a tag lookup on preferred site"""
    assert isinstance(tag, str), "str not " + str(type(tag))
    # remove whitespace at edges and replace whitespace with +
    tag = tag.strip().lower().replace(' ', '+')
    url = app_constants.DEFAULT_EHEN_URL
    if not url.endswith('/'):
        url += '/'

    if ':' not in tag:
        tag = 'misc:' + tag

    url += 'tag/' + tag

    open_web_link(url)
