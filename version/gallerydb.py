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
import functools
import io
import logging
import os
import queue
import threading
import uuid
from typing import Any, Callable, List, Union, Optional, Dict, Literal, ClassVar, Tuple, Set, Iterable

import scandir
from PyQt5.QtCore import QObject, pyqtSignal, QTime, pyqtBoundSignal
from dateutil import parser as dateparser

from .utils import (today, ArchiveFile, generate_img_hash, delete_path,
                    ARCHIVE_FILES, get_gallery_img, IMG_FILES, b_search)
from .database import db_constants
from .database import db
from .database.db import DBBase
from .executors import Executors

from . import app_constants
from . import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

method_queue = queue.PriorityQueue()
method_return = queue.Queue()
db_constants.METHOD_QUEUE = method_queue
db_constants.METHOD_RETURN = method_return


class PriorityObject:
    p: int
    data: Any

    def __init__(self, priority: int, data: Any):
        self.p = priority
        self.data = data

    def __lt__(self, other):
        return self.p < other.p


def process_methods():
    """
    Methods are objects.
    Put a list in the method queue where first index is the
    method. Named arguments are put in a dict.
    """
    while True:
        l = method_queue.get().data
        log_d('Processing a method from queue...')
        method = l.pop(0)
        log_d(method)
        args = []
        kwargs = {}
        get_args = 1
        no_return = False
        while get_args:
            try:
                a = l.pop(0)
                if a == 'no return':
                    no_return = True
                    continue
                if isinstance(a, dict):
                    kwargs = a
                else:
                    args.append(a)
            except IndexError:
                get_args = 0
        args = tuple(args)
        if args and kwargs:
            r = method(*args, **kwargs)
        elif args:
            r = method(*args)
        elif kwargs:
            r = method(**kwargs)
        else:
            r = method()
        if not no_return:
            method_return.put(r)
        method_queue.task_done()


method_queue_thread = threading.Thread(name='Method Queue Thread', target=process_methods,
                                       daemon=True)
method_queue_thread.start()


def execute(method: Callable, no_return: bool, *args, **kwargs) -> Any:
    log_d('Added method to queue')
    log_d('Method name: {}'.format(method.__name__))
    arg_list = [method]
    priority: int = kwargs.pop("priority", 999)
    if no_return:
        arg_list.append('no return')
    if args:
        for x in args:
            arg_list.append(x)
    if kwargs:
        arg_list.append(kwargs)
    method_queue.put(PriorityObject(priority, arg_list))
    if not no_return:
        return method_return.get()


def chapter_map(row, chapter: Chapter) -> Chapter:
    assert isinstance(chapter, Chapter)
    chapter.title = row['chapter_title']
    chapter.path = bytes.decode(row['chapter_path'])
    chapter.in_archive = row['in_archive']
    chapter.pages = row['pages']
    return chapter


def gallery_map(row, gallery, chapters=True, tags=True, hashes=True):
    gallery.title = row['title']
    gallery.artist = row['artist']
    gallery.profile = bytes.decode(row['profile'])
    gallery.path = bytes.decode(row['series_path'])
    gallery.is_archive = row['is_archive']
    try:
        gallery.path_in_archive = bytes.decode(row['path_in_archive'])
    except TypeError:
        pass
    gallery.info = row['info']
    gallery.language = row['language']
    gallery.rating = row['rating']
    gallery.status = row['status']
    gallery.type = row['type']
    gallery.fav = row['fav']

    def convert_date(date_str):
        # 2015-10-25 21:44:38
        if date_str and date_str != 'None':
            return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    gallery.pub_date = convert_date(row['pub_date'])
    gallery.last_read = convert_date(row['last_read'])
    gallery.date_added = convert_date(row['date_added'])
    gallery.times_read = row['times_read']
    gallery._db_v = row['db_v']
    gallery.exed = row['exed']
    gallery.view = row['view']
    try:
        gallery.link = bytes.decode(row['link'])
    except TypeError:
        gallery.link = row['link']

    if chapters:
        gallery.chapters = ChapterDB.get_chapters_for_gallery(gallery.id)

    if tags:
        gallery.tags = TagDB.get_gallery_tags(gallery.id)

    if hashes:
        gallery.hashes = HashDB.get_gallery_hashes(gallery.id)

    gallery.set_defaults()
    return gallery


def default_chap_exec(gallery_or_id: Union[Gallery, int], chap: Chapter, only_values=False) \
        -> Union[Tuple[str, dict], Tuple[int, Union[str, List[str]], int, bytes, int, Literal[0, 1]]]:
    """Pass a Gallery object or gallery id and a Chapter object"""
    gid: int
    if isinstance(gallery_or_id, Gallery):
        gallery: Gallery = gallery_or_id
        gid = gallery.id
        in_archive = gallery.is_archive
    else:
        gid = gallery_or_id
        in_archive = chap.in_archive

    if only_values:
        result_exec = (gid, chap.title, chap.number, str.encode(chap.path), chap.pages, in_archive)
    else:
        result_exec = (
            """
                INSERT INTO chapters(series_id, chapter_title, chapter_number, chapter_path, pages, in_archive)
                VALUES(:series_id, :chapter_title, :chapter_number, :chapter_path, :pages, :in_archive)""",
            {
                'series_id': gid,
                'chapter_title': chap.title,
                'chapter_number': chap.number,
                'chapter_path': str.encode(chap.path),
                'pages': chap.pages,
                'in_archive': in_archive
            }
        )
    return result_exec


def default_exec(obj: Gallery):
    obj.set_defaults()

    def object_or_none(maybe_none: Any) -> Union[None, Any]:
        if maybe_none == "None":
            return None
        else:
            return maybe_none

    executing = ["""INSERT INTO series(title, artist, profile, series_path, is_archive, path_in_archive,
                    info, type, fav, language, rating, status, pub_date, date_added, last_read, link,
                    times_read, db_v, exed, view)
                VALUES(:title, :artist, :profile, :series_path, :is_archive, :path_in_archive, :info, :type, :fav, 
                :language, :rating, :status, :pub_date, :date_added, :last_read, :link, :times_read, :db_v, :exed, 
                :view)""",
                 {
                     'title': object_or_none(obj.title),
                     'artist': object_or_none(obj.artist),
                     'profile': str.encode(obj.profile),
                     'series_path': str.encode(obj.path),
                     'is_archive': object_or_none(obj.is_archive),
                     'path_in_archive': str.encode(obj.path_in_archive),
                     'info': object_or_none(obj.info),
                     'fav': object_or_none(obj.fav),
                     'type': object_or_none(obj.type),
                     'language': object_or_none(obj.language),
                     'rating': object_or_none(obj.rating),
                     'status': object_or_none(obj.status),
                     'pub_date': object_or_none(obj.pub_date),
                     'date_added': object_or_none(obj.date_added),
                     'last_read': object_or_none(obj.last_read),
                     'link': str.encode(obj.link),
                     'times_read': object_or_none(obj.times_read),
                     'db_v': object_or_none(db_constants.REAL_DB_VERSION),
                     'exed': object_or_none(obj.exed),
                     'view': object_or_none(obj.view)
                 }]
    return executing


def only_once(fn) -> Callable[[Any, ...], GalleryModifier]:
    f_name = fn.__name__

    @functools.wraps(fn)
    def m(self: GalleryModifier, val: Any) -> GalleryModifier:
        if f_name in self._mem \
                and self._mem[f_name] == val:
            return self
        retval = fn(self, val)
        self._mem[f_name] = val
        self.executing[f_name] = retval
        return self

    return m


def update_series(fn) -> Callable[[Any, ...], GalleryModifier]:
    f_name = fn.__name__
    fn = only_once(fn)

    @functools.wraps(fn)
    def m(self: GalleryModifier, val) -> GalleryModifier:
        retval = fn(self, val)
        args = self.executing[f_name]
        if len(args) == 2:  # means that it changed
            db_name, value = args
            self.executing[f_name] = (self.UPDATE_SERIES, db_name, value)
        return retval

    return m


# needed for type hinting set_* methods to return
# GalleryModifier which is done with decorator magic
# noinspection PyTypeChecker
class GalleryModifier:
    """
    Builder class meant to easily modify a gallery in the db given its id.

    NOTE: Meant to replace GalleryDB.modify_gallery in certain uses.
    """
    # Cases
    UPDATE_SERIES: ClassVar[int] = 0
    MODIFY_TAGS: ClassVar[int] = 1
    UPDATE_CHAPTERS: ClassVar[int] = 2
    REBUILD_HASHES: ClassVar[int] = 3

    id: int

    def __init__(self, id: int):
        self.id = id
        self._mem = {}
        self.executing = {}
        self._done = False

    @update_series
    def set_title(self, title: str) -> GalleryModifier:
        return 'title', title

    @update_series
    def set_profile(self, profile: str) -> GalleryModifier:
        return 'profile', profile

    @update_series
    def set_artist(self, artist: str) -> GalleryModifier:
        return 'artist', artist

    @update_series
    def set_info(self, info: str) -> GalleryModifier:
        return 'info', info

    @update_series
    def set_type(self, gal_type: str) -> GalleryModifier:
        return 'type', gal_type

    @update_series
    def set_fav(self, fav: int) -> GalleryModifier:
        return 'fav', fav

    @update_series
    def set_language(self, language: str) -> GalleryModifier:
        return 'language', language

    @update_series
    def set_rating(self, rating: int) -> GalleryModifier:
        return 'rating', rating

    @update_series
    def set_status(self, status: str) -> GalleryModifier:
        return 'status', status

    @update_series
    def set_pub_date(self, pub_date: datetime) -> GalleryModifier:
        return 'pub_date', pub_date

    @update_series
    def set_link(self, link: str) -> GalleryModifier:
        return 'link', link

    @update_series
    def set_times_read(self, times_read: int) -> GalleryModifier:
        return 'times_read', times_read

    @update_series
    def set_last_read(self, last_read) -> GalleryModifier:
        return 'last_read', last_read

    @update_series
    def set_series_path(self, series_path: str) -> GalleryModifier:
        return 'series_path', series_path

    @update_series
    def set_db_v(self, db_v) -> GalleryModifier:
        return 'db_v', db_v

    @update_series
    def set_exed(self, exed) -> GalleryModifier:
        return 'exed', exed

    @update_series
    def set_is_archive(self, is_archive) -> GalleryModifier:
        return 'is_archive', is_archive

    @update_series
    def set_path_in_archive(self, path_in_archive) -> GalleryModifier:
        return 'path_in_archive', path_in_archive

    @update_series
    def set_view(self, view) -> GalleryModifier:
        return 'view', view

    @update_series
    def set_date_added(self, date_added) -> GalleryModifier:
        return 'date_added', date_added

    @only_once
    def set_tags(self, tags: Dict) -> GalleryModifier:
        return self.MODIFY_TAGS, tags

    @only_once
    def set_chapters(self, chapters: ChaptersContainer) -> GalleryModifier:
        return self.UPDATE_CHAPTERS, chapters

    # hashes type hint based on GalleryDB.rebuild_gallery
    # type check, TODO: i suspect that might not be the correct type
    @only_once
    def set_hashes(self, hashes: Gallery) -> GalleryModifier:
        return self.REBUILD_HASHES, hashes

    def execute(self) -> None:
        if self._done:
            raise RuntimeError("GalleryModifier with id {} was already done.".format(self.id))
        self._done = True

        buffer = []
        values = []
        # 2020-11-09: i dont really know if you need the delayed execution
        # of the not-UPDATE_SERIES cases, but it appeared in that order
        # in the GalleryDB.modify_gallery
        procs = []
        for query in self.executing.values():
            case, *args = query
            if case == self.UPDATE_SERIES:
                db_name, val = args
                buffer.append('{}=?'.format(db_name))
                values.append(val)
            elif case == self.MODIFY_TAGS:
                tags = args[0]
                procs.append(lambda: TagDB.modify_tags(self.id, tags))
            elif case == self.UPDATE_CHAPTERS:
                chapters = args[0]
                procs.append(lambda: ChapterDB.update_chapter(chapters))
            elif case == self.REBUILD_HASHES:
                hashes = args[0]
                procs.append(lambda: HashDB.rebuild_gallery_hashes(hashes))
            else:
                raise ValueError('Unknown Case {}, args: {}.'.format(case, args))

        if buffer:
            values.append(self.id)
            stmt = 'UPDATE series SET {} WHERE series_id=? ;'.format(', '.join(buffer))
            GalleryDB.execute(stmt, tuple(values))

        for proc in procs:
            proc()

    @classmethod
    def from_gallery(cls, gallery: Gallery, only_include: Optional[Iterable[str]] = None) -> GalleryModifier:
        """
        Returns a GalleryModifier object with all its field set to the corresponding values from gallery.
        Pass only_include an iterable of strings to only copy those fields while excluding the rest.
        """
        default = [
            'title', 'artist', 'info', 'type', 'fav', 'tags', 'language', 'rating', 'status', 'pub_date', 'link',
            'times_read', 'last_read', 'exed', 'is_archive', 'path_in_archive', 'view', 'profile', 'date_added',
            'chapters', 'hashes'
        ]
        if only_include:
            if not all(x in default for x in only_include):
                raise ValueError(
                    "invalid sequence of attributes, {}. Can not build GalleryModifier from gallery."
                        .format([x for x in only_include if x not in default])
                )
        else:
            only_include = default

        attrs = only_include
        obj = cls(gallery.id)
        for attr in attrs:
            getattr(obj, 'set_' + attr)(getattr(gallery, attr))
        return obj


# TODO: Changed uses of GalleryModifier.from_gallery and GalleryDB.new_gallery_modifier_based_on with this subclass.
class GalleryInheritedModifier(GalleryModifier):
    """
    Given the gallery passed to its constructor it allows to set default values for the fields easily for further
    edition, by allowing to `inherit` fields from said gallery.

    ## Usage:
    modifier = (
        GalleryInheritedModifier(gallery)
        .inherit_title() # same as calling .set_title(gallery.title)
        .inherit_tags()  # same as calling .set_tags(gallery.tags)
    ).execute()

    And so on... Although it handles some nuances, where the name of the attribute is not the same in the Gallery object
    and the Gallery schema in the db.
    """
    gallery: Gallery

    def __init__(self, gallery: Gallery):
        super().__init__(gallery.id)
        self.gallery = gallery

    def inherit_title(self) -> GalleryInheritedModifier:
        return self.set_title(self.gallery.title)

    def inherit_profile(self) -> GalleryInheritedModifier:
        return self.set_profile(self.gallery.profile)

    def inherit_artist(self) -> GalleryInheritedModifier:
        return self.set_artist(self.gallery.artist)

    def inherit_info(self) -> GalleryInheritedModifier:
        return self.set_info(self.gallery.info)

    def inherit_type(self) -> GalleryInheritedModifier:
        return self.set_type(self.gallery.type)

    def inherit_fav(self) -> GalleryInheritedModifier:
        return self.set_fav(self.gallery.fav)

    def inherit_language(self) -> GalleryInheritedModifier:
        return self.set_language(self.gallery.language)

    def inherit_rating(self) -> GalleryInheritedModifier:
        return self.set_rating(self.gallery.rating)

    def inherit_status(self) -> GalleryInheritedModifier:
        return self.set_status(self.gallery.status)

    def inherit_pub_date(self) -> GalleryInheritedModifier:
        return self.set_pub_date(self.gallery.pub_date)

    def inherit_link(self) -> GalleryInheritedModifier:
        return self.set_link(self.gallery.link)

    def inherit_times_read(self) -> GalleryInheritedModifier:
        return self.set_times_read(self.gallery.times_read)

    def inherit_last_read(self) -> GalleryInheritedModifier:
        return self.set_last_read(self.gallery.last_read)

    def inherit_exed(self) -> GalleryInheritedModifier:
        return self.set_exed(self.gallery.exed)

    def inherit_is_archive(self) -> GalleryInheritedModifier:
        return self.set_is_archive(self.gallery.is_archive)

    def inherit_path_in_archive(self) -> GalleryInheritedModifier:
        return self.set_path_in_archive(self.gallery.path_in_archive)

    def inherit_view(self) -> GalleryInheritedModifier:
        return self.set_view(self.gallery.view)

    def inherit_date_added(self) -> GalleryInheritedModifier:
        return self.set_date_added(self.gallery.date_added)

    def inherit_tags(self) -> GalleryInheritedModifier:
        return self.set_tags(self.gallery.tags)

    def inherit_chapters(self) -> GalleryInheritedModifier:
        return self.set_chapters(self.gallery.chapters)

    def inherit_hashes(self) -> GalleryInheritedModifier:
        return self.set_hashes(self.gallery)

    def inherit_series_path(self) -> GalleryInheritedModifier:
        return self.set_series_path(self.gallery.path)

    # @formatter: off
    def inherit_all(self) -> GalleryInheritedModifier:
        return (
            self
                .inherit_title()
                .inherit_profile()
                .inherit_artist()
                .inherit_info()
                .inherit_type()
                .inherit_fav()
                .inherit_language()
                .inherit_rating()
                .inherit_status()
                .inherit_pub_date()
                .inherit_link()
                .inherit_times_read()
                .inherit_last_read()
                .inherit_exed()
                .inherit_is_archive()
                .inherit_path_in_archive()
                .inherit_view()
                .inherit_date_added()
                .inherit_tags()
                .inherit_chapters()
                .inherit_hashes()
        )
    # @formatter: on


class GalleryDB(DBBase):
    """
    Provides the following s methods:
        rebuild_thumb -> Rebuilds gallery thumbnail
        rebuild_galleries -> Rebuilds the galleries in DB
        modify_gallery -> Modifies gallery with given gallery id
        get_all_gallery -> returns a list of all gallery (<Gallery> class) currently in DB
        get_gallery_by_path -> Returns gallery with given path
        get_gallery_by_id -> Returns gallery with given id
        add_gallery -> adds gallery into db
        set_gallery_title -> changes gallery title
        gallery_count -> returns amount of gallery (can be used for indexing)
        del_gallery -> deletes the gallery with the given id recursively
        check_exists -> Checks if provided string exists
        clear_thumb -> Deletes a thumbnail
        clear_thumb_dir -> Dletes everything in the thumbnail directory
    """

    def __init__(self):
        raise Exception("GalleryDB should not be instantiated")

    @staticmethod
    def rebuild_thumb(gallery: Gallery) -> bool:
        """Rebuilds gallery thumbnail"""
        try:
            log_i('Recreating thumb {}'.format(gallery.title.encode(errors='ignore')))
            if gallery.profile:
                GalleryDB.clear_thumb(gallery.profile)
            gallery.profile = Executors.generate_thumbnail(gallery, blocking=True)
            GalleryDB.new_gallery_modifier_based_on(gallery).inherit_profile().execute()
        except:
            log.exception("Failed rebuilding thumbnail")
            return False
        return True

    @staticmethod
    def clear_thumb(path: Union[str, 'os.PathLike']) -> None:
        """Deletes a thumbnail"""
        try:
            if os.path.samefile(path, app_constants.NO_IMAGE_PATH):
                return
        except FileNotFoundError:
            pass

        try:
            if os.path.isfile(path):
                os.unlink(path)
        except:
            log.exception('Failed to delete thumb {}'.format(os.path.split(path)[1].encode(errors='ignore')))

    @staticmethod
    def clear_thumb_dir() -> None:
        """Deletes everything in the thumbnail directory"""
        if os.path.exists(db_constants.THUMBNAIL_PATH):
            for thumbfile in scandir.scandir(db_constants.THUMBNAIL_PATH):
                GalleryDB.clear_thumb(thumbfile.path)

    @staticmethod
    def rebuild_gallery(gallery: Gallery, thumb=False) -> bool:
        """Rebuilds the galleries in DB"""
        try:
            log_i('Rebuilding {}'.format(gallery.title.encode(errors='ignore')))
            log_i("Rebuilding gallery {}".format(gallery.id))
            HashDB.del_gallery_hashes(gallery.id)

            attr_include = [
                'title', 'artist', 'info', 'type', 'fav', 'tags', 'language', 'rating', 'status',
                'pub_date', 'link', 'times_read', 'last_read', 'exed', 'is_archive', 'path_in_archive', 'view'
            ]
            # @formatter: off
            (
                GalleryModifier
                    .from_gallery(gallery, only_include=attr_include)
                    .set_db_v(db_constants.CURRENT_DB_VERSION)
                    .execute()
            )
            # @formatter: on
            if thumb:
                GalleryDB.rebuild_thumb(gallery)
        except:
            log.exception('Failed rebuilding')
            return False
        return True

    @classmethod
    def new_gallery_modifier_based_on(cls, gallery: Gallery) -> GalleryInheritedModifier:
        """
        Returns a GalleryModifier object with all its field set to the corresponding values from gallery.

        Equivalent to calling gallery in `GalleryInheritedModifier`.
        """
        return GalleryInheritedModifier(gallery)

    @classmethod
    def new_gallery_modifier(cls, gallery_or_id: Union[Gallery, int]) -> GalleryModifier:
        """
        Returns a GalleryModifier object, initialized with the passed id or gallery's id.
        """
        if isinstance(gallery_or_id, Gallery):
            return GalleryModifier(gallery_or_id.id)
        elif isinstance(gallery_or_id, int):
            return GalleryModifier(gallery_or_id)

        raise TypeError("expected GalleryModifier or int, got {}.".format(gallery_or_id))

    @classmethod
    def modify_gallery(cls, series_id, title=None, profile=None, artist=None, info=None, type=None, fav=None,
                       tags=None, language=None, rating=None, status=None, pub_date=None, link=None,
                       times_read=None, last_read=None, series_path=None, chapters=None, _db_v=None,
                       hashes=None, exed=None, is_archive=None, path_in_archive=None, view=None, date_added=None):
        """Modifies gallery with given gallery id"""
        assert isinstance(series_id, int)
        assert not isinstance(series_id, bool)
        executing = []
        if title is not None:
            assert isinstance(title, str)
            executing.append(["UPDATE series SET title=? WHERE series_id=?", (title, series_id)])
        if profile is not None:
            assert isinstance(profile, str)
            executing.append(["UPDATE series SET profile=? WHERE series_id=?", (str.encode(profile), series_id)])
        if artist is not None:
            assert isinstance(artist, str)
            executing.append(["UPDATE series SET artist=? WHERE series_id=?", (artist, series_id)])
        if info is not None:
            assert isinstance(info, str)
            executing.append(["UPDATE series SET info=? WHERE series_id=?", (info, series_id)])
        if type is not None:
            assert isinstance(type, str)
            executing.append(["UPDATE series SET type=? WHERE series_id=?", (type, series_id)])
        if fav is not None:
            assert isinstance(fav, int)
            executing.append(["UPDATE series SET fav=? WHERE series_id=?", (fav, series_id)])
        if language is not None:
            assert isinstance(language, str)
            executing.append(["UPDATE series SET language=? WHERE series_id=?", (language, series_id)])
        if rating is not None:
            assert isinstance(rating, int)
            executing.append(["UPDATE series SET rating=? WHERE series_id=?", (rating, series_id)])
        if status is not None:
            assert isinstance(status, str)
            executing.append(["UPDATE series SET status=? WHERE series_id=?", (status, series_id)])
        if pub_date is not None:
            executing.append(["UPDATE series SET pub_date=? WHERE series_id=?", (pub_date, series_id)])
        if link is not None:
            executing.append(["UPDATE series SET link=? WHERE series_id=?", (link, series_id)])
        if times_read is not None:
            executing.append(["UPDATE series SET times_read=? WHERE series_id=?", (times_read, series_id)])
        if last_read is not None:
            executing.append(["UPDATE series SET last_read=? WHERE series_id=?", (last_read, series_id)])
        if series_path is not None:
            executing.append(
                ["UPDATE series SET series_path=? WHERE series_id=?", (str.encode(series_path), series_id)])
        if _db_v is not None:
            executing.append(["UPDATE series SET db_v=? WHERE series_id=?", (_db_v, series_id)])
        if exed is not None:
            executing.append(["UPDATE series SET exed=? WHERE series_id=?", (exed, series_id)])
        if is_archive is not None:
            executing.append(["UPDATE series SET is_archive=? WHERE series_id=?", (is_archive, series_id)])
        if path_in_archive is not None:
            executing.append(["UPDATE series SET path_in_archive=? WHERE series_id=?", (path_in_archive, series_id)])
        if view is not None:
            executing.append(["UPDATE series SET view=? WHERE series_id=?", (view, series_id)])
        if date_added is not None:
            executing.append(["UPDATE series SET date_added=? WHERE series_id=?", (date_added, series_id)])

        if tags is not None:
            assert isinstance(tags, dict)
            TagDB.modify_tags(series_id, tags)
        if chapters is not None:
            assert isinstance(chapters, ChaptersContainer)
            ChapterDB.update_chapter(chapters)

        if hashes is not None:
            assert isinstance(hashes, Gallery)
            HashDB.rebuild_gallery_hashes(hashes)

        for query in executing:
            cls.execute(*query)

    @classmethod
    def get_all_gallery(cls, chapters: bool = True, tags: bool = True, hashes: bool = True):
        """
        Careful, might crash with very large libraries i think...
        Returns a list of all galleries (<Gallery> class) currently in DB
        """
        cursor = cls.execute('SELECT * FROM series')
        all_gallery = cursor.fetchall()
        return GalleryDB.gen_galleries(all_gallery, chapters, tags, hashes)

    @staticmethod
    def gen_galleries(gallery_dict, chapters=True, tags=True, hashes=True):
        """
        Map galleries fetched from DB
        """
        gallery_list = []
        for gallery_row in gallery_dict:
            gallery = Gallery()
            gallery.id = gallery_row['series_id']
            gallery = gallery_map(gallery_row, gallery, chapters, tags, hashes)
            if not os.path.exists(gallery.path):
                gallery.dead_link = True
            ListDB.query_gallery(gallery)
            gallery_list.append(gallery)

        return gallery_list

    @classmethod
    def get_gallery_by_path(cls, path):
        """Returns gallery with given path"""
        assert isinstance(path, str), "Provided path is invalid"
        cursor = cls.execute('SELECT * FROM series WHERE series_path=?', (str.encode(path),))
        row = cursor.fetchone()
        try:
            gallery = Gallery()
            gallery.id = row['series_id']
            gallery = gallery_map(row, gallery)
            return gallery
        except TypeError:
            return None

    @classmethod
    def get_gallery_by_id(cls, id):
        """Returns gallery with given id"""
        assert isinstance(id, int), "Provided ID is invalid"
        cursor = cls.execute('SELECT * FROM series WHERE series_id=?', (id,))
        row = cursor.fetchone()
        gallery = Gallery()
        try:
            gallery.id = row['series_id']
            gallery = gallery_map(row, gallery)
            return gallery
        except TypeError:
            return None

    @classmethod
    def add_gallery(cls, gallery: Gallery, test_mode=False) -> None:
        """A gallery object and appends it to DB"""
        assert isinstance(gallery, Gallery), "add_gallery method only accepts gallery items"
        log_i('Recevied gallery: {}'.format(gallery.path.encode(errors='ignore')))

        # TODO: implement mass gallery adding!  User execute_many method for
        # effeciency!

        cursor = cls.execute(*default_exec(gallery))
        series_id = cursor.lastrowid
        gallery.id = series_id
        if not gallery.profile:
            Executors.generate_thumbnail(gallery, on_method=gallery.set_profile)
        if gallery.tags:
            TagDB.add_tags(gallery)
        ChapterDB.add_chapters(gallery)

    @classmethod
    def gallery_count(cls) -> int:
        """
        Returns the amount of galleries in db.
        """
        cursor = cls.execute("SELECT count(*) AS 'size' FROM series")
        return cursor.fetchone()['size']

    @classmethod
    def del_gallery(cls, list_of_gallery: List[Gallery], local=False) -> None:
        """Deletes all galleries in the list recursively."""
        assert isinstance(list_of_gallery, list), "Please provide a valid list of galleries to delete"
        for gallery in list_of_gallery:
            if local:
                app_constants.TEMP_PATH_IGNORE.append(os.path.normcase(gallery.path))
                if gallery.is_archive:
                    s = delete_path(gallery.path)
                else:
                    paths = [x.path for x in gallery.chapters]
                    [app_constants.TEMP_PATH_IGNORE.append(os.path.normcase(x)) for x in paths]  # to avoid data race?
                    for chap, path in enumerate(paths):
                        s = delete_path(path)
                        if not s:
                            log_e('Failed to delete chapter {}:{}, {}'.format(chap,
                                                                              gallery.id,
                                                                              gallery.title.encode('utf-8', 'ignore')))
                            continue
                    s = delete_path(gallery.path)

                if not s:
                    log_e('Failed to delete gallery:{}, {}'.format(gallery.id,
                                                                   gallery.title.encode('utf-8', 'ignore')))
                    continue

            GalleryDB.clear_thumb(gallery.profile)
            cls.execute('DELETE FROM series WHERE series_id=?', (gallery.id,))
            gallery.id = None
            log_i('Successfully deleted: {}'.format(gallery.title.encode('utf-8', 'ignore')))
            app_constants.NOTIF_BAR.add_text('Successfully deleted: {}'.format(gallery.title))

    @staticmethod
    def check_exists(name, galleries=None, filter=True):
        """
        Checks if provided string exists in provided sorted
        list based on path name.
        Note: key will be normcased
        """
        # pdb.set_trace()
        if galleries is None:
            galleries = app_constants.GALLERY_DATA + app_constants.GALLERY_ADDITION_DATA
            filter = True

        if filter:
            filter_list = []
            for gallery in galleries:
                filter_list.append(os.path.normcase(gallery.path))
            filter_list = sorted(filter_list)
        else:
            filter_list = galleries

        search = b_search(filter_list, os.path.normcase(name))
        return search


class ChapterDB(DBBase):
    """
    Provides the following database methods:
        update_chapter -> Updates an existing chapter in DB
        add_chapter -> adds chapter into db
        add_chapter_raw -> links chapter to the given seires id, and adds into db
        get_chapters_for_gallery -> returns a dict with chapters linked to the given series_id
        get_chapter-> returns a dict with chapter matching the given chapter_number
        get_chapter_id -> returns id of the chapter number
        chapter_size -> returns amount of manga (can be used for indexing)
        del_all_chapters <- Deletes all chapters with the given series_id
        del_chapter <- Deletes chapter with the given number from gallery
    """

    def __init__(self):
        raise Exception("ChapterDB should not be instantiated")

    @classmethod
    def update_chapter(cls, chapter_container: ChaptersContainer,
                       numbers: Optional[Union[List[int], Tuple[int]]] = None):
        """
        Updates an existing chapter in DB.
        Pass a gallery's ChapterContainer, specify number with a list of ints
        leave empty to update all chapters.
        """
        if numbers is None:
            numbers = []
        assert isinstance(chapter_container, ChaptersContainer) and isinstance(numbers, (list, tuple))
        if numbers:
            chapters = []
            for n in numbers:
                chapters.append(chapter_container[n])
        else:
            chapters = chapter_container.get_all_chapters()

        executing = []
        for chap in chapters:
            new_path = chap.path
            executing.append(
                (chap.title, str.encode(new_path), chap.pages, chap.in_archive, chap.gallery.id, chap.number,))

        cls.executemany(
            "UPDATE chapters SET chapter_title=?, chapter_path=?, pages=?, in_archive=? WHERE series_id=? AND chapter_number=?",
            executing)

    @classmethod
    def add_chapters(cls, gallery_object):
        """Adds chapters linked to gallery into database"""
        assert isinstance(gallery_object, Gallery), "Parent gallery need to be of class Gallery"
        series_id = gallery_object.id
        executing = []
        for chap in gallery_object.chapters:
            executing.append(default_chap_exec(gallery_object, chap, True))
        if not executing:
            raise Exception
        cls.executemany('INSERT INTO chapters VALUES(NULL, ?, ?, ?, ?, ?, ?)', executing)

    @classmethod
    def add_chapters_raw(cls, series_id, chapters_container: ChaptersContainer):
        """Adds chapter(s) to a gallery with the received series_id"""
        assert isinstance(chapters_container,
                          ChaptersContainer), "chapters_container must be of class ChaptersContainer"
        executing = []
        for chap in chapters_container:
            if not ChapterDB.get_chapter(series_id, chap.number):
                executing.append(default_chap_exec(series_id, chap, True))
            else:
                ChapterDB.update_chapter(chapters_container, [chap.number])

        cls.executemany('INSERT INTO chapters VALUES(NULL, ?, ?, ?, ?, ?, ?)', executing)

    @classmethod
    def get_chapters_for_gallery(cls, series_id):
        """
        Returns a ChaptersContainer of chapters matching the received series_id
        """
        assert isinstance(series_id, int), "Please provide a valid gallery ID"
        cursor = cls.execute('SELECT * FROM chapters WHERE series_id=?', (series_id,))
        rows = cursor.fetchall()
        chapters = ChaptersContainer()

        for row in rows:
            chap = chapters.create_chapter(row['chapter_number'])
            chapter_map(row, chap)
        return chapters

    @classmethod
    def get_chapter(cls, series_id, chap_numb):
        """Returns a ChaptersContainer of chapters matching the recieved chapter_number
        return None for no match
        """
        assert isinstance(chap_numb, int), "Please provide a valid chapter number"
        cursor = cls.execute('SELECT * FROM chapters WHERE series_id=? AND chapter_number=?',
                             (series_id, chap_numb,))
        try:
            rows = cursor.fetchall()
            chapters = ChaptersContainer()
            for row in rows:
                chap = chapters.create_chapter(row['chapter_number'])
                chapter_map(row, chap)
        except TypeError:
            return None
        return chapters

    @classmethod
    def get_chapter_id(cls, series_id: int, chapter_number: int) -> Optional[int]:
        """Returns id of the chapter number"""
        assert isinstance(series_id, int) and isinstance(chapter_number, int), \
            "Passed args must be of int not {} and {}".format(type(series_id), type(chapter_number))
        cursor = cls.execute('SELECT chapter_id FROM chapters WHERE series_id=? AND chapter_number=?',
                             (series_id, chapter_number,))
        try:
            row = cursor.fetchone()
            chp_id = row['chapter_id']
            return chp_id
        except KeyError:
            return None
        except TypeError:
            return None

    @staticmethod
    def chapter_size(gallery_id):
        """Returns the amount of chapters for the given
        gallery id
        """
        pass

    @classmethod
    def del_all_chapters(cls, series_id):
        """Deletes all chapters with the given series_id"""
        assert isinstance(series_id, int), "Please provide a valid gallery ID"
        cls.execute('DELETE FROM chapters WHERE series_id=?', (series_id,))

    @classmethod
    def del_chapter(cls, series_id, chap_number):
        """Deletes chapter with the given number from gallery"""
        assert isinstance(series_id, int), "Please provide a valid gallery ID"
        assert isinstance(chap_number, int), "Please provide a valid chapter number"
        cls.execute('DELETE FROM chapters WHERE series_id=? AND chapter_number=?',
                    (series_id, chap_number,))


class TagDB(DBBase):
    """
    Tags are returned in a dict where {"namespace":["tag1","tag2"]}
    The namespace "default" will be used for tags without namespaces.

    Provides the following methods:
    del_tags <- Deletes the tags with corresponding tag_ids from DB
    del_gallery_tags_mapping <- Deletes the tags and gallery mappings with corresponding series_ids from DB
    get_gallery_tags -> Returns all tags and namespaces found for the given series_id;
    get_tag_gallery -> Returns all galleries with the given tag
    get_ns_tags -> "Returns a dict with namespace as key and list of tags as value"
    get_ns_tags_to_gallery -> Returns all galleries linked to the namespace tags. Receives a dict like this: {"namespace":["tag1","tag2"]}
    get_tags_from_namespace -> Returns all galleries linked to the namespace
    add_tags <- Adds the given dict_of_tags to the given series_id
    modify_tags <- Modifies the given tags
    get_all_tags -> Returns all tags in database
    get_all_ns -> Returns all namespaces in database
    """

    def __init__(self):
        raise Exception("TagsDB should not be instantiated")

    @staticmethod
    def del_tags(list_of_tags_id):
        """Deletes the tags with corresponding tag_ids from DB"""
        pass

    @classmethod
    def del_gallery_mapping(cls, series_id):
        """Deletes the tags and gallery mappings with corresponding series_ids from DB"""
        assert isinstance(series_id, int), "Please provide a valid gallery id"

        # delete all mappings related to the given series_id
        cls.execute('DELETE FROM series_tags_map WHERE series_id=?', [series_id])

    @classmethod
    def get_gallery_tags(cls, series_id):
        """Returns all tags and namespaces found for the given series_id"""
        if not isinstance(series_id, int):
            return {}
        cursor = cls.execute('SELECT tags_mappings_id FROM series_tags_map WHERE series_id=?',
                             (series_id,))
        tags = {}
        result = cursor.fetchall()
        for tag_map_row in result:  # iterate all tag_mappings_ids
            try:
                if not tag_map_row:
                    continue
                # get tag and namespace
                c = cls.execute('SELECT namespace_id, tag_id FROM tags_mappings WHERE tags_mappings_id=?',
                                (tag_map_row['tags_mappings_id'],))
                for row in c.fetchall():  # iterate all rows
                    # get namespace
                    c = cls.execute('SELECT namespace FROM namespaces WHERE namespace_id=?',
                                    (row['namespace_id'],))
                    try:
                        namespace = c.fetchone()['namespace']
                    except TypeError:
                        continue

                    # get tag
                    c = cls.execute('SELECT tag FROM tags WHERE tag_id=?', (row['tag_id'],))
                    try:
                        tag = c.fetchone()['tag']
                    except TypeError:
                        continue

                    # add them to dict
                    if not namespace in tags:
                        tags[namespace] = [tag]
                    else:
                        # namespace already exists in dict
                        tags[namespace].append(tag)
            except IndexError:
                continue
        return tags

    @classmethod
    def add_tags(cls, obj):
        """Adds the given dict_of_tags to the given series_id"""
        assert isinstance(obj, Gallery), "Please provide a valid gallery of class gallery"

        series_id = obj.id
        dict_of_tags = obj.tags

        def look_exists(tag_or_ns, what):
            """check if tag or namespace already exists in base
            returns id, else returns None"""
            c = cls.execute('SELECT {}_id FROM {}s WHERE {} = ?'.format(what, what, what),
                            (tag_or_ns,))
            try:  # exists
                return c.fetchone()['{}_id'.format(what)]
            except TypeError:  # doesnt exist
                return None
            except IndexError:
                return None

        tags_mappings_id_list = []
        # first let's add the tags and namespaces to db
        for namespace in dict_of_tags:
            tags_list = dict_of_tags[namespace]
            # don't add if it already exists
            try:
                namespace_id = look_exists(namespace, "namespace")
                if not namespace_id:
                    raise ValueError
            except ValueError:
                c = cls.execute('INSERT INTO namespaces(namespace) VALUES(?)', (namespace,))
                namespace_id = c.lastrowid

            tags_id_list = []
            for tag in tags_list:
                try:
                    tag_id = look_exists(tag, "tag")
                    if not tag_id:
                        raise ValueError
                except ValueError:
                    c = cls.execute('INSERT INTO tags(tag) VALUES(?)', (tag,))
                    tag_id = c.lastrowid

                tags_id_list.append(tag_id)

            def look_exist_tag_map(tag_id):
                """Checks DB if the tag_id already exists with the namespace_id, returns id else None"""
                c = cls.execute('SELECT tags_mappings_id FROM tags_mappings WHERE namespace_id=? AND tag_id=?',
                                (namespace_id, tag_id,))
                try:  # exists
                    return c.fetchone()['tags_mappings_id']
                except TypeError:  # doesnt exist
                    return None
                except IndexError:
                    return None

            # time to map the tags to the namespace now
            for tag_id in tags_id_list:
                # First check if tags mappings exists
                try:
                    t_map_id = look_exist_tag_map(tag_id)
                    if t_map_id:
                        tags_mappings_id_list.append(t_map_id)
                    else:
                        raise TypeError
                except TypeError:
                    c = cls.execute('INSERT INTO tags_mappings(namespace_id, tag_id) VALUES(?, ?)',
                                    (namespace_id, tag_id,))
                    # add the tags_mappings_id to our list
                    tags_mappings_id_list.append(c.lastrowid)

        # Lastly we map the series_id to the tags_mappings
        executing = []
        for tags_map in tags_mappings_id_list:
            executing.append((series_id, tags_map,))
            # cls.execute(cls, 'INSERT INTO series_tags_map(series_id, tags_mappings_id)
            # VALUES(?, ?)', (series_id, tags_map,))
        cls.executemany('INSERT OR IGNORE INTO series_tags_map(series_id, tags_mappings_id) VALUES(?, ?)',
                        executing)

    @staticmethod
    def modify_tags(series_id, dict_of_tags):
        """Modifies the given tags"""

        # We first delete all mappings
        TagDB.del_gallery_mapping(series_id)

        # Now we add the new tags to DB
        weak_gallery = Gallery()
        weak_gallery.id = series_id
        weak_gallery.tags = dict_of_tags

        TagDB.add_tags(weak_gallery)

    @staticmethod
    def get_tag_gallery(tag):
        """Returns all galleries with the given tag"""
        pass

    @classmethod
    def get_ns_tags(cls):
        """Returns a dict of all tags with namespace as key and list of tags as value"""
        cursor = cls.execute('SELECT namespace_id, tag_id FROM tags_mappings')
        ns_tags = {}
        ns_id_history = {}  # to avoid unesseccary DB fetching
        for t in cursor.fetchall():
            try:
                # get namespace
                if not t['namespace_id'] in ns_id_history:
                    c = cls.execute('SELECT namespace FROM namespaces WHERE namespace_id=?', (t['namespace_id'],))
                    ns = c.fetchone()['namespace']
                    ns_id_history[t['namespace_id']] = ns
                else:
                    ns = ns_id_history[t['namespace_id']]
                # get tag
                c = cls.execute('SELECT tag FROM tags WHERE tag_id=?', (t['tag_id'],))
                tag = c.fetchone()['tag']
                # put in dict
                if ns in ns_tags:
                    ns_tags[ns].append(tag)
                else:
                    ns_tags[ns] = [tag]
            except:
                continue
        return ns_tags

    @staticmethod
    def get_tags_from_namespace(namespace):
        """Returns a dict with namespace as key and list of tags as value"""
        pass

    @staticmethod
    def get_ns_tags_to_gallery(ns_tags):
        """
        Returns all galleries linked to the namespace tags.
        Receives a dict like this: {"namespace":["tag1","tag2"]}
        """
        pass

    @classmethod
    def get_all_tags(cls):
        """
        Returns all tags in database in a list
        """
        cursor = cls.execute('SELECT tag FROM tags')
        tags = [t['tag'] for t in cursor.fetchall()]
        return tags

    @classmethod
    def get_all_ns(cls):
        """
        Returns all namespaces in database in a list
        """
        cursor = cls.execute('SELECT namespace FROM namespaces')
        ns = [n['namespace'] for n in cursor.fetchall()]
        return ns


class ListDB(DBBase):
    """
    """

    @classmethod
    def init_lists(cls):
        """Creates and returns lists fetched from DB"""
        lists = []
        c = cls.execute('SELECT * FROM list')
        list_rows = c.fetchall()
        for l_row in list_rows:
            l = GalleryList(l_row['list_name'], filter=l_row['list_filter'], id=l_row['list_id'])
            if l_row['type'] == GalleryList.COLLECTION:
                l.type = GalleryList.COLLECTION
            elif l_row['type'] == GalleryList.REGULAR:
                l.type = GalleryList.REGULAR
            profile = l_row['profile']
            if profile:
                l.profile = bytes.decode(profile)
            l.enforce = bool(l_row['enforce'])
            l.regex = bool(l_row['regex'])
            l.case = bool(l_row['l_case'])
            l.strict = bool(l_row['strict'])
            lists.append(l)
            app_constants.GALLERY_LISTS.add(l)

        return lists

    @classmethod
    def query_gallery(cls, gallery):
        """Maps gallery to the correct lists"""

        c = cls.execute('SELECT list_id FROM series_list_map WHERE series_id=?', (gallery.id,))
        list_rows = [x['list_id'] for x in c.fetchall()]
        for l in app_constants.GALLERY_LISTS:
            if l._id in list_rows:
                l.add_gallery(gallery, False, _check_filter=False)

    @classmethod
    def modify_list(cls, gallery_list: GalleryList):
        assert isinstance(gallery_list, GalleryList)
        if gallery_list.id:
            cls.execute("""UPDATE list SET list_name=?, list_filter=?, profile=?,
               type=?, enforce=?, regex=?, l_case=?, strict=? WHERE list_id=?""",
                        (gallery_list.name, gallery_list.filter, str.encode(gallery_list.profile),
                         gallery_list.type, int(gallery_list.enforce), int(gallery_list.regex), int(gallery_list.case),
                         int(gallery_list.strict), gallery_list.id))

    @classmethod
    def add_list(cls, gallery_list: GalleryList):
        """Adds a list of GalleryList class to DB"""
        assert isinstance(gallery_list, GalleryList)
        if gallery_list.id:
            ListDB.modify_list(gallery_list)
        else:
            c = cls.execute("""INSERT INTO list(list_name, list_filter, profile, type,
                            enforce, regex, l_case, strict) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                gallery_list.name, gallery_list.filter, str.encode(gallery_list.profile),
                                gallery_list.type,
                                int(gallery_list.enforce), int(gallery_list.regex), int(gallery_list.case),
                                int(gallery_list.strict)))
            gallery_list._id = c.lastrowid

        ListDB.add_gallery_to_list(gallery_list.galleries(), gallery_list)

    @classmethod
    def _g_id_or_list(cls, gallery_or_id_or_list: Union[Gallery, int, List[Gallery], List[int]]) -> List[int]:
        """Returns gallery ids"""
        if isinstance(gallery_or_id_or_list, (Gallery, int)):
            gallery_or_id_or_list = [gallery_or_id_or_list]

        return [g.id if isinstance(g, Gallery) else g for g in gallery_or_id_or_list]

    @classmethod
    def add_gallery_to_list(cls, gallery_or_id_or_list: Union[Gallery, int, List[Gallery], List[int]],
                            gallery_list: GalleryList) -> None:
        """Maps provided gallery or list of galleries or gallery id to list"""
        assert isinstance(gallery_list, GalleryList)
        g_ids = cls._g_id_or_list(gallery_or_id_or_list)

        values = [(gallery_list.id, x) for x in g_ids]
        cls.executemany('INSERT OR IGNORE INTO series_list_map(list_id, series_id) VALUES(?, ?)', values)

    @classmethod
    def remove_list(cls, gallery_list):
        """Deletes list from DB"""
        assert isinstance(gallery_list, GalleryList)
        if gallery_list.id:
            cls.execute('DELETE FROM list WHERE list_id=?', (gallery_list.id,))
        try:
            app_constants.GALLERY_LISTS.remove(gallery_list)
        except KeyError:
            pass

    @classmethod
    def remove_gallery_from_list(cls, gallery_or_id_or_list: Union[Gallery, int, List[int]], gallery_list: GalleryList):
        """Removes provided gallery or list of galleries or gallery id from list"""
        assert isinstance(gallery_list, GalleryList)
        if gallery_list.id:
            g_ids = ListDB._g_id_or_list(gallery_or_id_or_list)

            values = [(gallery_list.id, x) for x in g_ids]
            cls.executemany('DELETE FROM series_list_map WHERE list_id=? AND series_id=?', values)


class HashDB(DBBase):
    """
    Contains the following methods:

    find_gallery -> returns galleries which matches the given list of hashes
    get_gallery_hashes -> returns all hashes with the given gallery id in a list
    get_gallery_hash -> returns hash of chapter specified. If page is specified, returns hash of chapter page
    gen_gallery_hashes <- generates hashes for gallery's chapters and inserts them to db
    rebuild_gallery_hashes <- inserts hashes into DB only if it doesnt already exist
    """

    @classmethod
    def find_gallery(cls, hashes: List):
        assert isinstance(hashes, list)
        gallery_ids = {}
        hash_status = []
        for hash in hashes:
            r = cls.execute('SELECT series_id FROM hashes WHERE hash=?', (hash,))
            try:
                g_ids = r.fetchall()
                for r in g_ids:
                    g_id = r['series_id']
                    if g_id not in gallery_ids:
                        gallery_ids[g_id] = 1
                    else:
                        gallery_ids[g_id] = gallery_ids[g_id] + 1
                if g_ids:
                    hash_status.append(True)
                else:
                    hash_status.append(False)
            except KeyError:
                hash_status.append(False)
            except TypeError:
                hash_status.append(False)

        if all(hash_status):
            # the one with most matching hashes
            g_id = None
            h_match_count = 0
            for g in gallery_ids:
                gallery_id = gallery_ids[g]
                if gallery_id > h_match_count:
                    h_match_count = gallery_id
                    g_id = g
            if g_id:
                weak_gallery = Gallery()
                weak_gallery.id = g_id
                return weak_gallery

        return None

    @classmethod
    def get_gallery_hashes(cls, gallery_id: int) -> List[bytes]:
        """Returns all hashes with the given gallery id in a list"""
        cursor = cls.execute('SELECT hash FROM hashes WHERE series_id=?',
                             (gallery_id,))
        hashes = []
        try:
            for row in cursor.fetchall():
                hashes.append(row['hash'])
        except IndexError:
            return []
        return hashes

    @classmethod
    def get_gallery_hash(cls, gallery_id: int, chapter: int, page: Optional[int] = None) -> Optional[List[bytes]]:
        """
        returns hash of chapter. If page is specified, returns hash of chapter page
        """
        assert isinstance(gallery_id, int)
        assert isinstance(chapter, int)
        if page:
            assert isinstance(page, int)
        chap_id = ChapterDB.get_chapter_id(gallery_id, chapter)
        if not chap_id:
            return None
        if page:
            exceuting = ["SELECT hash FROM hashes WHERE series_id=? AND chapter_id=? AND page=?",
                         (gallery_id, chap_id, page)]
        else:
            exceuting = ["SELECT hash FROM hashes WHERE series_id=? AND chapter_id=?",
                         (gallery_id, chap_id)]
        hashes = []
        c = cls.execute(*exceuting)
        for h in c.fetchall():
            try:
                hashes.append(h['hash'])
            except KeyError:
                pass
        return hashes

    @classmethod
    def gen_gallery_hash(cls, gallery: Gallery, chapter: int, page: Union[int, str, List, None] = None, color_img=False,
                         _name=None) -> Union[Dict[Union[int, str], Union[bytes, str, 'os.PathLike']], Iterable[bytes]]:
        """
        Generate hash for a specific chapter.
        Set page to only generate specific page
        page: 'mid' or number or list of numbers
        color_img: if true then a hash to colored img will be returned if possible
        Returns dict with chapter number or 'mid' as key and hash as value
        """
        assert isinstance(gallery, Gallery)
        assert isinstance(chapter, int)
        if page is not None:
            assert isinstance(page, (int, str, list))
        skip_gen = False
        chap_id = None
        hashes = {}
        if gallery.id is not None:
            chap_id = ChapterDB.get_chapter_id(gallery.id, chapter)

            c = cls.execute('SELECT hash, page FROM hashes WHERE series_id=? AND chapter_id=?',
                            (gallery.id, chap_id,))
            hashes = {}
            for r in c.fetchall():
                try:
                    if r['hash'] and r['page'] is not None:
                        hashes[r['page']] = r['hash']
                except TypeError:
                    pass
            if isinstance(page, (int, list)):
                if isinstance(page, int):
                    _page = [page]
                else:
                    _page = page
                h = {}
                t = False
                for p in _page:
                    if p in hashes:
                        h[p] = hashes[p]
                    else:
                        t = True
                if not t:
                    skip_gen = True
                    hashes = h

            elif gallery.chapters[chapter].pages == len(hashes.keys()):
                skip_gen = True
                if page == "mid":
                    try:
                        hashes = {'mid': hashes[len(hashes) // 2]}
                    except KeyError:
                        skip_gen = False

        if not skip_gen or color_img:

            def look_exists(page):
                """check if hash already exists in database
                returns hash, else returns None"""
                c = cls.execute('SELECT hash FROM hashes WHERE page=? AND chapter_id=?',
                                (page, chap_id,))
                try:  # exists
                    return c.fetchone()['hash']
                except TypeError:  # doesnt exist
                    return None
                except IndexError:
                    return None

            if gallery.dead_link:
                log_e("Could not generate hash of dead gallery: {}".format(gallery.title.encode(errors='ignore')))
                return {}

            try:
                chap = gallery.chapters[chapter]
            except KeyError:
                utils.make_chapters(gallery)
                try:
                    chap = gallery.chapters[chapter]
                except KeyError:
                    return {}

            executing = []
            try:
                if gallery.is_archive:
                    raise NotADirectoryError
                imgs = sorted([x.path for x in scandir.scandir(chap.path) if x.path.lower().endswith(utils.IMG_FILES)])
                pages = {}
                for n, i in enumerate(imgs):
                    pages[n] = i

                if page is not None:
                    pages = {}
                    if color_img:
                        # if first img is colored, then return filepath of that
                        if not utils.image_greyscale(imgs[0]):
                            return {'color': imgs[0]}
                    if page == 'mid':
                        imgs = imgs[len(imgs) // 2]
                        pages[len(imgs) // 2] = imgs
                    elif isinstance(page, list):
                        try:
                            for p in page:
                                pages[p] = imgs[p]
                        except IndexError:
                            raise app_constants.InternalPagesMismatch
                    else:
                        imgs = imgs[page]
                        pages = {page: imgs}

                hashes = {}
                if gallery.id is not None:
                    for p in pages:
                        h = look_exists(p)
                        if not h:
                            with open(pages[p], 'rb') as f:
                                h = generate_img_hash(f)
                            executing.append((h, gallery.id, chap_id, p,))
                        hashes[p] = h
                else:
                    for i in pages:
                        with open(pages[i], 'rb') as f:
                            hashes[i] = generate_img_hash(f)

            except NotADirectoryError:
                _temp_dir = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
                is_archive = gallery.is_archive
                try:
                    if is_archive:
                        f_zip = ArchiveFile(gallery.path)
                    else:
                        f_zip = ArchiveFile(chap.path)
                except app_constants.CreateArchiveFail:
                    log_e('Could not generate hash: CreateZipFail')
                    return {}

                pages = {}
                if page is not None:
                    con = sorted(f_zip.dir_contents(chap.path))
                    if color_img:
                        # if first img is colored, then return hash of that
                        f_bytes = io.BytesIO(f_zip.open(con[0], False))
                        if not utils.image_greyscale(f_bytes):
                            return {'color': f_zip.extract(con[0])}
                        f_bytes.close()
                    if page == 'mid':
                        p = len(con) // 2
                        img = con[p]
                        pages = {p: f_zip.open(img, True)}
                    elif isinstance(page, list):
                        for x in page:
                            pages[x] = f_zip.open(con[x], True)
                    else:
                        p = page
                        img = con[p]
                        pages = {p: f_zip.open(img, True)}

                else:
                    imgs = sorted(f_zip.dir_contents(chap.path))
                    for n, img in enumerate(imgs):
                        pages[n] = f_zip.open(img, True)
                f_zip.close()

                hashes = {}
                if gallery.id is not None:
                    for p in pages:
                        h = look_exists(p)
                        if not h:
                            h = generate_img_hash(pages[p])
                            executing.append((h, gallery.id, chap_id, p,))
                        hashes[p] = h
                else:
                    for i in pages:
                        hashes[i] = generate_img_hash(pages[i])

            if executing:
                cls.executemany('INSERT INTO hashes(hash, series_id, chapter_id, page) VALUES(?, ?, ?, ?)',
                                executing)

        if page == 'mid':
            r_hash = {'mid': list(hashes.values())[0]}
        else:
            r_hash = hashes

        if _name is not None:
            try:
                r_hash[_name] = r_hash[page]
            except KeyError:
                pass
        return r_hash

    @classmethod
    def gen_gallery_hashes(cls, gallery: Gallery) -> List[bytes]:
        """Generates hashes for gallery's first chapter and inserts them to DB"""
        # noinspection PyTypeChecker
        gallery_hash: List[bytes] = HashDB.gen_gallery_hash(gallery, 0)
        return gallery_hash

    @staticmethod
    def rebuild_gallery_hashes(gallery: Gallery) -> List[bytes]:
        """Inserts hashes into DB only if it doesnt already exist"""
        assert isinstance(gallery, Gallery)
        hashes = HashDB.get_gallery_hashes(gallery.id)

        if not hashes:
            hashes = HashDB.gen_gallery_hashes(gallery)
        return hashes

    @classmethod
    def del_gallery_hashes(cls, gallery_id):
        """Deletes all hashes linked to the given gallery id"""
        cls.execute('DELETE FROM hashes WHERE series_id=?', (gallery_id,))


class GalleryList:
    """
    Provides access to lists..
    methods:
    - add_gallery <- adds a gallery of Gallery class to list
    - remove_gallery <- removes galleries matching the provided gallery id
    - clear <- removes all galleries from the list
    - galleries -> returns a list with all galleries in list
    - scan <- scans for galleries matching the listfilter and adds them to gallery
    """
    # types
    REGULAR: ClassVar[int] = 0
    COLLECTION: ClassVar[int] = 1

    _galleries: Set[Gallery]
    _id: Optional[int]

    def __init__(self, name, list_of_galleries: List[Gallery] = None, filter=None, id=None, _db=True):
        if list_of_galleries is None:
            list_of_galleries = []
        self._id = id  # shouldnt ever be touched
        self.name = name
        self.profile = ''
        self.type = self.REGULAR
        self.filter = filter
        self.enforce = False
        self.regex = False
        self.case = False
        self.strict = False
        self._galleries = set()
        self._ids_chache = []
        self._scanning = False
        self.add_gallery(list_of_galleries, _db)

    @property
    def id(self):
        return self._id

    def add_gallery(self, gallery_or_list_of: Union[List[Gallery], Gallery], _db=True, _check_filter=True):
        """add_gallery <- adds a gallery of Gallery class to list"""
        assert isinstance(gallery_or_list_of, (Gallery, list))
        if isinstance(gallery_or_list_of, Gallery):
            gallery_or_list_of = [gallery_or_list_of]
        if _check_filter and self.filter and self.enforce:
            execute(self.scan, True, gallery_or_list_of)
            return
        new_galleries = []
        for gallery in gallery_or_list_of:
            self._galleries.add(gallery)
            if not utils.b_search(self._ids_chache, gallery.id):
                new_galleries.append(gallery)
                self._ids_chache.append(gallery.id)
                # uses timsort algorithm so it's ok
                self._ids_chache.sort()
        if _db:
            execute(ListDB.add_gallery_to_list, True, new_galleries, self)

    def remove_gallery(self, gallery_id_or_list_of: Union[int, List[int]]) -> None:
        """remove_gallery <- removes galleries matching the provided gallery id"""
        if isinstance(gallery_id_or_list_of, int):
            gallery_id_or_list_of = [gallery_id_or_list_of]
        g_ids = gallery_id_or_list_of
        g_ids_to_delete = []
        g_to_delete = []
        for g in self._galleries:
            if g.id in g_ids:
                g_to_delete.append(g)
                try:
                    self._ids_chache.remove(g.id)
                except ValueError:
                    pass
                g_ids_to_delete.append(g.id)
        for g in g_to_delete:
            self._galleries.remove(g)
        execute(ListDB.remove_gallery_from_list, True, g_ids_to_delete, self)

    def clear(self) -> None:
        """removes all galleries from the list"""
        if self._galleries:
            execute(ListDB.remove_gallery_from_list, True, list(self._galleries), self)
        self._galleries.clear()
        self._ids_chache.clear()

    def galleries(self) -> List[Gallery]:
        """returns a list with all galleries in list"""
        return list(self._galleries)

    def __contains__(self, g):
        return utils.b_search(self._ids_chache, g.id)

    def add_to_db(self):
        app_constants.GALLERY_LISTS.add(self)
        execute(ListDB.add_list, True, self)

    def scan(self, galleries=None):
        if self.filter and not self._scanning:
            self._scanning = True
            if isinstance(galleries, Gallery):
                galleries = [galleries]
            if not galleries:
                galleries = app_constants.GALLERY_DATA
            new_galleries = []
            filter_term = ' '.join(self.filter.split())
            args = []
            if self.regex:
                args.append(app_constants.Search.Regex)
            if self.case:
                args.append(app_constants.Search.Case)
            if self.strict:
                args.append(app_constants.Search.Strict)
            search_pieces = utils.get_terms(filter_term)

            def _search_g(gallery):
                all_terms = {t: False for t in search_pieces}

                for t in search_pieces:
                    if gallery.contains(t, args):
                        all_terms[t] = True

                if all(all_terms.values()):
                    return True
                return False

            for gallery in galleries:
                if _search_g(gallery):
                    new_galleries.append(gallery)

            if self.enforce:
                g_to_remove = []
                for g in self.galleries():
                    if not _search_g(g):
                        g_to_remove.append(g.id)
                if g_to_remove:
                    self.remove_gallery(g_to_remove)
            self.add_gallery(new_galleries, _check_filter=False)
            self._scanning = False

    def __lt__(self, other):
        return self.name < other.name


class Gallery:
    """
    Base class for a gallery.
    Available data:
    id -> Not to be editied. Do not touch.
    title <- [list of titles] or str
    profile <- path to thumbnail
    path <- path to gallery
    artist <- str
    chapters <- {<number>:<path>} # probably lying, likely is ChaptersContainer
    chapter_size <- int of number of chapters
    info <- str
    fav <- int (1 for true 0 for false)
    rating <- float
    type <- str (Manga? Doujin? Other?)
    language <- str
    status <- "unknown", "completed" or "ongoing"
    tags <- list of str???? probably meant dict with str keys
    pub_date <- date
    date_added <- date, will be defaulted to today if not specified
    last_read <- timestamp (e.g. time.time())
    times_read <- an integer telling us how many times the gallery has been opened
    hashes <- a list of hashes of the gallery's chapters
    exed <- indicator on if gallery metadata has been fetched
    valid <- a bool indicating the validity of the gallery

    Takes ownership of ChaptersContainer

    2020-11-08:
    Originally this project did not have type hinting. Some type hinting might
    be wrong as is being added after what is written above.
    TODO: Correct any types that dont correspond, especially date date_added,
    """
    id: Optional[int]
    title: Union[str, List[str]]
    profile: Union[str, 'os.PathLike']
    _path: Union[str, 'os.PathLike']
    artist: str
    chapters: Dict[int, Union[str, 'os.PathLike']]
    chapters_size: int
    info: str
    FAV_HINT: ClassVar = Literal[0, 1]
    fav: FAV_HINT
    rating: float
    type: str
    language: str
    STATUS_HINT: ClassVar = Literal['unknown', 'completed', 'ongoing', '']
    status: STATUS_HINT
    tags: Dict[str, Any]
    pub_date: Optional[datetime]
    date_added: datetime
    last_read: Any  # DOnt know
    times_read: int
    hashes: List[bytes]
    exed: Any  # Dont really know for now
    valid: bool

    _chapters: ChaptersContainer
    file_type: str

    def __init__(self):

        self.id = None  # Will be defaulted.
        self.title = ""
        self.profile = ""
        self._path = ""
        self.path_in_archive = ""
        self.is_archive = 0
        self.artist = ""
        self._chapters = ChaptersContainer(self)
        self.info = ""
        self.fav = 0
        self.rating = 0.0
        self.type = ""
        self.link = ""
        self.language = ""
        self.status = ""
        self.tags = {}
        self.pub_date = None
        self.date_added = datetime.datetime.now().replace(microsecond=0)
        self.last_read = None
        self.times_read = 0
        self.valid = False
        self._db_v = None
        self.hashes = []
        self.exed = 0
        self.file_type = "folder"
        self.view = app_constants.ViewType.Default  # default view

        self._grid_visible = False
        self._list_view_selected = False
        self._profile_qimage = {}
        self._profile_load_status = {}
        self.dead_link = False
        self.state = app_constants.GalleryState.Default
        self.qtime = QTime()  # used by views to record addition

    @property
    def path(self) -> Union[str, 'os.PathLike']:
        return self._path

    @path.setter
    def path(self, n_p: Union[str, 'os.PathLike']):
        self._path = n_p
        _, ext = os.path.splitext(n_p)
        if ext:
            self.file_type = ext[1:].lower()  # remove dot

    def set_defaults(self):
        if not self.type:
            self.type = app_constants.G_DEF_TYPE.capitalize()
        if not self.language:
            self.language = app_constants.G_DEF_LANGUAGE.capitalize()
        if not self.status:
            self.status = app_constants.G_DEF_STATUS.capitalize()

    def reset_profile(self) -> None:
        self._profile_load_status.clear()
        self._profile_qimage.clear()

    def _profile_loaded(self, img, ptype=None, method=None):
        self._profile_load_status[ptype] = img
        if method and img:
            method(self, img)

    def get_profile(self, ptype, on_method=None):
        psize = app_constants.THUMB_DEFAULT
        if ptype == app_constants.ProfileType.Small:
            psize = app_constants.THUMB_SMALL

        if ptype in self._profile_qimage:
            f = self._profile_qimage[ptype]
            if not f.done():
                return
            if f.result():
                return f.result()
        img = self._profile_load_status.get(ptype)
        if not img:
            self._profile_qimage[ptype] = Executors.load_thumbnail(self.profile, psize,
                                                                   on_method=self._profile_loaded,
                                                                   ptype=ptype, method=on_method)

        return img

    def set_profile(self, future):
        """set with profile with future object"""
        self.profile = future.result()
        if self.id is not None:
            modifier = GalleryDB.new_gallery_modifier(self.id).set_profile(self.profile)
            execute(modifier.execute, True, priority=0)

    @property
    def chapters(self) -> ChaptersContainer:
        return self._chapters

    @chapters.setter
    def chapters(self, chp_cont: ChaptersContainer) -> None:
        assert isinstance(chp_cont, ChaptersContainer)
        chp_cont.set_parent(self)
        self._chapters = chp_cont

    def merge(self, galleries):
        """Merge galleries into this galleries, adding them as chapters"""
        pass

    def gen_hashes(self):
        """Generate hashes while inserting them into DB"""
        if not self.hashes:
            hsh = HashDB.gen_gallery_hashes(self)
            if hsh:
                self.hashes = hsh
                return True
            else:
                return False
        else:
            return True

    def validate(self) -> bool:
        """Validates gallery, returns status"""
        # TODO: Extend this
        validity = []
        status = False

        # if not self.hashes:
        #	HashDB.gen_gallery_hashes(self)
        #	self.hashes = HashDB.get_gallery_hashes(self.id)

        if all(validity):
            status = True
            self.valid = True
        return status

    def invalidities(self):
        """
        Checks all attributes for invalidities.
        Returns list of string with invalid attribute names
        """
        return []

    def _keyword_search(self, ns, tag, args: Optional[List] = None):
        if args is None:
            args = []
        term = ''
        lt, gt = range(2)

        def _search(term) -> bool:
            if app_constants.Search.Regex in args:
                if utils.regex_search(tag, term, args):
                    return True
            else:
                if app_constants.DEBUG:
                    log_d("{} {}".format(tag, term))
                if utils.search_term(tag, term, args):
                    return True
            return False

        def _operator_parse(tag):
            o = None
            if tag:
                if tag[0] == '<':
                    o = lt
                    tag = tag[1:]
                elif tag[0] == '>':
                    o = gt
                    tag = tag[1:]
            return tag, o

        def _operator_supported(attr, date=False):
            try:
                o_tag, o = _operator_parse(tag)
                if date:
                    o_tag = dateparser.parse(o_tag, dayfirst=True)
                    if o_tag:
                        o_tag = o_tag.date()
                else:
                    o_tag = int(o_tag)
                if o != None:
                    if o == gt:
                        return o_tag < attr
                    elif o == lt:
                        return o_tag > attr
                else:
                    return o_tag == attr
            except ValueError:
                return False

        if ns == 'Title':
            term = self.title
        elif ns in ['Language', 'Lang']:
            term = self.language
        elif ns == 'Type':
            term = self.type
        elif ns == 'Status':
            term = self.status
        elif ns == 'Artist':
            term = self.artist
        elif ns == 'Url':
            term = self.link
        elif ns in ['Descr', 'Description']:
            term = self.info
        elif ns in ['Chapter', 'Chapters']:
            return _operator_supported(self.chapters.count())
        elif ns in ['Read_count', 'Read count', 'Times_read', 'Times read']:
            return _operator_supported(self.times_read)
        elif ns in ['Rating', 'Stars']:
            return _operator_supported(self.rating)
        elif ns in ['Date_added', 'Date added']:
            return _operator_supported(self.date_added.date(), True)
        elif ns in ['Pub_date', 'Publication', 'Pub date']:
            if self.pub_date:
                return _operator_supported(self.pub_date.date(), True)
            return False
        elif ns in ['Last_read', 'Last read']:
            if self.last_read:
                return _operator_supported(self.last_read.date(), True)
            return False
        return _search(term)

    def __contains__(self, key):
        assert isinstance(key, Chapter), "Can only check for chapters in gallery"
        return self.chapters.__contains__(key)

    def contains(self, key, args: Optional[List] = None) -> bool:
        """Check if gallery contains keyword"""
        if args is None:
            args = []
        is_exclude = False if key[0] == '-' else True
        key = key[1:] if not is_exclude else key
        default = False if is_exclude else True
        if key:
            # check in title/artist/language
            found = False
            if not ':' in key:
                for g_attr in [self.title, self.artist, self.language]:
                    if not g_attr:
                        continue
                    if app_constants.Search.Regex in args:
                        if utils.regex_search(key, g_attr, args=args):
                            found = True
                            break
                    else:
                        if utils.search_term(key, g_attr, args=args):
                            found = True
                            break

            # check in tag
            if not found:
                tags = key.split(':')
                ns = tag = ''
                # only namespace is lowered and capitalized for now
                if len(tags) > 1:
                    ns = tags[0].lower().capitalize()
                    tag = tags[1]
                else:
                    tag = tags[0]

                # very special keywords
                if ns:
                    key_word = ['none', 'null']
                    if ns == 'Tag' and tag in key_word:
                        if not self.tags or len(self.tags) == 1 and 'default' in self.tags and not self.tags['default']:
                            return is_exclude
                    elif ns == 'Artist' and tag in key_word:
                        if not self.artist:
                            return is_exclude
                    elif ns == 'Status' and tag in key_word:
                        if not self.status or self.status == 'Unknown':
                            return is_exclude
                    elif ns == 'Language' and tag in key_word:
                        if not self.language:
                            return is_exclude
                    elif ns == 'Url' and tag in key_word:
                        if not self.link:
                            return is_exclude
                    elif ns in ('Descr', 'Description') and tag in key_word:
                        if not self.info or self.info == 'No description..':
                            return is_exclude
                    elif ns == 'Type' and tag in key_word:
                        if not self.type:
                            return is_exclude
                    elif ns in ('Publication', 'Pub_date', 'Pub date') and tag in key_word:
                        if not self.pub_date:
                            return is_exclude
                    elif ns == 'Path' and tag in key_word:
                        if self.dead_link:
                            return is_exclude

                if app_constants.Search.Regex in args:
                    if ns:
                        if self._keyword_search(ns, tag, args=args):
                            return is_exclude

                        for x in self.tags:
                            if utils.regex_search(ns, x):
                                for t in self.tags[x]:
                                    if utils.regex_search(tag, t, True, args=args):
                                        return is_exclude
                    else:
                        for x in self.tags:
                            for t in self.tags[x]:
                                if utils.regex_search(tag, t, True, args=args):
                                    return is_exclude
                else:
                    if ns:
                        if self._keyword_search(ns, tag, args=args):
                            return is_exclude

                        if ns in self.tags:
                            for t in self.tags[ns]:
                                if utils.search_term(tag, t, True, args=args):
                                    return is_exclude
                    else:
                        for x in self.tags:
                            for t in self.tags[x]:
                                if utils.search_term(tag, t, True, args=args):
                                    return is_exclude
            else:
                return is_exclude
        return default

    def move_gallery(self, new_path=''):
        log_i("Moving gallery...")
        log_d("Old gallery path: {}".format(self.path))
        old_head, old_tail = os.path.split(self.path)
        try:
            self.path = utils.move_files(self.path, new_path)
        except PermissionError:
            log.exception("Failed to move gallery")
            app_constants.NOTIF_BAR.add_text("Permission Error: Failed to move gallery ({})".format(self.title))
            return
        new_head, new_tail = os.path.split(self.path)
        for chap in self.chapters:
            if not chap.in_archive:
                head, tail = os.path.split(chap.path)
                log_d("old chapter path: {}".format(chap.path))
                if os.path.exists(os.path.join(self.path, tail)):
                    chap.path = os.path.join(self.path, tail)
                    continue
                if os.path.join(old_head, old_tail) == os.path.join(head, tail):
                    chap.path = self.path
                    continue

                if self.is_archive:
                    utils.move_files(chap.path, os.path.join(new_head, tail))
                else:
                    utils.move_files(chap.path, os.path.join(self.path, tail))

    def __lt__(self, other):
        if hasattr(other, 'id'):
            return self.id < other.id
        return super().__lt__(other)

    def __str__(self):
        s = ""
        for x in sorted(self.__dict__):
            s += "{:>20}: {:>15}\n".format(x, str(self.__dict__[x]))
        return s


class Chapter:
    """
    Base class for a chapter
    Contains following attributes:
    parent -> The ChapterContainer it belongs in
    gallery -> The Gallery it belongs to
    title -> title of chapter
    path -> path to chapter
    number -> chapter number
    pages -> chapter pages
    in_archive -> 1 if the chapter path is in an archive else 0
    """
    parent: ChaptersContainer
    gallery: Gallery
    title: Union[str, List[str]]  # based on docstring of Gallery
    path: Union[str, 'os.PathLike']
    number: int
    pages: int
    in_archive: Literal[0, 1]

    def __init__(self, parent: ChaptersContainer, gallery: Gallery, number: int = 0,
                 path: Union[str, 'os.PathLike'] = '', pages: int = 0, in_archive: Literal[0, 1] = 0, title: str = ''):
        self.parent = parent
        self.gallery = gallery
        self.title = title
        self.path = path
        self.number = number
        self.pages = pages
        self.in_archive = in_archive

    def __lt__(self, other):
        if hasattr(other, 'number'):
            return self.number < other.number
        return super().__lt__(other)

    def __str__(self):
        s = """
        Chapter: {0.number}
        Title: {0.title}
        Path: {0.path}
        Pages: {0.pages}
        in_archive: {0.in_archive}
        """.format(self)
        return s

    @property
    def next_chapter(self) -> Optional[Chapter]:
        if self.number + 1 < len(self.parent):
            return self.parent[self.number + 1]
        else:
            return None

    @property
    def previous_chapter(self) -> Optional[Chapter]:
        if self.number - 1 >= 0:
            return self.parent[self.number - 1]
        else:
            return None

    def open(self, stat_msg: bool = True) -> None:
        if stat_msg:
            txt = "Opening chapter {} of {}".format(self.number + 1, self.gallery.title)
            app_constants.STAT_MSG_METHOD(txt)
            app_constants.NOTIF_BAR.add_text(txt)
        if self.in_archive:
            if self.gallery.is_archive:
                execute(utils.open_chapter, True, self.path, self.gallery.path)
            else:
                execute(utils.open_chapter, True, '', self.path)
        else:
            execute(utils.open_chapter, True, self.path)
        self.gallery.times_read += 1
        self.gallery.last_read = datetime.datetime.now().replace(microsecond=0)
        modifier = GalleryDB.new_gallery_modifier_based_on(self.gallery).inherit_times_read().inherit_last_read()
        execute(modifier.execute, True)


class ChaptersContainer:
    """
    A container for chapters.
    Acts like a list/dict of chapters.

    Iterable returns a ordered list of chapters
    Sets to gallery.chapters
    """

    parent: Optional[Gallery]
    _data: Dict[int, Chapter]

    def __init__(self, gallery: Optional[Gallery] = None):
        self.parent = None
        self._data = {}

        if gallery:
            gallery.chapters = self

    def set_parent(self, gallery: Optional[Gallery]) -> None:
        assert isinstance(gallery, Gallery) or gallery is None
        self.parent = gallery
        for n in self._data:
            chap = self._data[n]
            chap.gallery = gallery

    def add_chapter(self, chp: Chapter, overwrite: bool = True, db=False) -> None:
        """Add a chapter of Chapter class to this container"""
        assert isinstance(chp, Chapter), "Chapter must be an instantiated Chapter class"

        if not overwrite:
            if chp.number in self._data:
                raise app_constants.ChapterExists

        chp.gallery = self.parent
        chp.parent = self
        self[chp.number] = chp

        if db:
            # TODO: implement this
            pass

    def create_chapter(self, number: Optional[int] = None) -> Chapter:
        """
        Creates Chapter class with the next chapter number or passed number arg and adds to container
        The chapter will be returned
        """
        if number is not None:
            chp = Chapter(self, self.parent, number=number)
            self[number] = chp
        else:
            next_number = 0
            for n in list(self._data.keys()):
                if n > next_number:
                    next_number = n
                else:
                    next_number += 1
            chp = Chapter(self, self.parent, number=next_number)
            self[next_number] = chp
        return chp

    def update_chapter_pages(self, number) -> bool:
        """Returns status on success"""
        if self.parent.dead_link:
            return False
        execute(HashDB.del_gallery_hashes, True, self.parent.id)
        chap = self[number]
        if chap.in_archive:
            _archive = utils.ArchiveFile(chap.gallery.path)
            chap.pages = len([x for x in _archive.dir_contents(chap.path) if x.lower().endswith(IMG_FILES)])
            _archive.close()
        else:
            chap.pages = len([x for x in scandir.scandir(chap.path) if x.path.lower().endswith(IMG_FILES)])

        execute(ChapterDB.update_chapter, True, self, [chap.number])
        return True

    def pages(self) -> int:
        """Returns the sum of all pages from every chapter contained."""
        p = 0
        for c in self:
            p += c.pages
        return p

    def get_chapter(self, number: int):
        if number in self._data:
            return self[number]
        else:
            raise KeyError("ChaptersContainer does not have chapter {}.".format(number))

    def get_all_chapters(self):
        return list(self._data.values())

    def count(self) -> int:
        return len(self)

    def pop(self, key, default: Any = None) -> Union[Chapter, Any]:
        return self._data.pop(key, default)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError("a subscript for ChapterContainer should be int, got {}.".format(key))

        if key in self._data:
            return self._data[key]

        raise KeyError("key {} not found in ChapterContainer.".format(key))

    def __setitem__(self, key, value):
        assert isinstance(key, int), "Key must be a chapter number"
        assert isinstance(value, Chapter), "Value must be an instantiated Chapter class"

        if value.gallery != self.parent:
            raise app_constants.ChapterWrongParentGallery
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self[c] for c in sorted(self._data.keys()))

    def __bool__(self):
        return bool(self._data)

    def __str__(self):
        s = ""
        for c in self:
            s += '\n' + '{}'.format(c)
        if not s:
            return '{}'
        return s

    def __contains__(self, key):
        if isinstance(key, Chapter):
            if key.gallery == self.parent and key in self._data.values():
                return True
            return False

        raise TypeError("expected type: 'Chapter', got key {} with type {}.".format(key, key.__class__))


class AdminDB(QObject):
    DONE: pyqtBoundSignal = pyqtSignal(bool)
    PROGRESS: pyqtBoundSignal = pyqtSignal(int)
    DATA_COUNT: pyqtBoundSignal = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

    def from_v021_to_v022(self, old_db_path=db_constants.DB_PATH):
        log_i("Started rebuilding database")
        if DBBase._DB_CONN:
            DBBase._DB_CONN.close()
        DBBase._DB_CONN = db.init_db(old_db_path)
        db_galleries = execute(GalleryDB.get_all_gallery, False, False, True, True)
        galleries = []
        for g in db_galleries:
            if not os.path.exists(g.path):
                log_i("Gallery doesn't exist anymore: {}".format(g.title.encode(errors="ignore")))
            else:
                galleries.append(g)

        n_galleries = []
        # get all chapters
        log_i("Getting chapters...")
        chap_rows = DBBase.execute("SELECT * FROM chapters").fetchall()
        data_count = len(chap_rows) * 2
        self.DATA_COUNT.emit(data_count)
        for n, chap_row in enumerate(chap_rows, -1):
            log_d('Next chapter row')
            for gallery in galleries:
                if gallery.id == chap_row['series_id']:
                    log_d('Found gallery for chapter row')
                    chaps = ChaptersContainer(gallery)
                    chap = chaps.create_chapter(chap_row['chapter_number'])
                    c_path = bytes.decode(chap_row['chapter_path'])
                    if c_path:
                        try:
                            t = utils.title_parser(os.path.split(c_path)[1])['title']
                        except IndexError:
                            t = c_path
                    else:
                        t = ''
                    chap.title = t
                    chap.path = c_path
                    chap.in_archive = chap_row['in_archive']
                    if gallery.is_archive:
                        zip = utils.ArchiveFile(gallery.path)
                        chap.pages = len(zip.dir_contents(chap.path))
                        zip.close()
                    else:
                        chap.pages = len(list(scandir.scandir(gallery.path)))
                    n_galleries.append(gallery)
                    galleries.remove(gallery)
                    break
            self.PROGRESS.emit(n)
        log_d("G: {} C:{}".format(len(n_galleries), data_count - 1))
        log_i("Database magic...")
        if os.path.exists(db_constants.THUMBNAIL_PATH):
            for root, dirs, files in scandir.walk(db_constants.THUMBNAIL_PATH, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

        head = os.path.split(old_db_path)[0]
        DBBase._DB_CONN.close()
        t_db_path = os.path.join(head, 'temp.db')
        conn = db.init_db(t_db_path)
        DBBase._DB_CONN = conn
        for n, g in enumerate(n_galleries, len(chap_rows) - 1):
            log_d('Adding new gallery')
            GalleryDB.add_gallery(g)
            self.PROGRESS.emit(n)

        conn.commit()
        conn.close()

        log_i("Cleaning up...")
        if os.path.exists(old_db_path):
            utils.backup_database(old_db_path)
            os.remove(old_db_path)
        if os.path.exists(db_constants.DB_PATH):
            os.remove(db_constants.DB_PATH)

        os.rename(t_db_path, db_constants.DB_PATH)
        self.PROGRESS.emit(data_count)
        log_i("Finished rebuilding database")
        self.DONE.emit(True)
        return True

    def rebuild_database(self):
        """Rebuilds database"""
        log_i("Initiating database rebuild")
        utils.backup_database()
        log_i("Getting galleries...")
        galleries = GalleryDB.get_all_gallery()
        self.DATA_COUNT.emit(len(galleries))
        db.DBBase._DB_CONN.close()
        log_i("Removing old database...")
        log_i("Creating new database...")
        temp_db = os.path.join(db_constants.DB_ROOT, "happypanda_temp.db")
        if os.path.exists(temp_db):
            os.remove(temp_db)
        db.DBBase._DB_CONN = db.init_db(temp_db)
        DBBase.begin()
        log_i("Adding galleries...")
        GalleryDB.clear_thumb_dir()
        for n, g in enumerate(galleries):
            if not os.path.exists(g.path):
                log_i("Gallery doesn't exist anymore: {}".format(g.title.encode(errors="ignore")))
            else:
                GalleryDB.add_gallery(g)
            self.PROGRESS.emit(n)
        DBBase.end()
        DBBase._DB_CONN.close()
        os.remove(db_constants.DB_PATH)
        os.rename(temp_db, db_constants.DB_PATH)
        db.DBBase._DB_CONN = db.init_db(db_constants.DB_PATH)
        self.PROGRESS.emit(len(galleries))
        log_i("Succesfully rebuilt database")
        self.DONE.emit(True)
        return True

    def rebuild_galleries(self):
        galleries = execute(GalleryDB.get_all_gallery, False)
        if galleries:
            self.DATA_COUNT.emit(len(galleries))
            log_i('Rebuilding galleries')
            for n, g in enumerate(galleries, 1):
                execute(GalleryDB.rebuild_gallery, False, g)
                self.PROGRESS.emit(n)
        self.DONE.emit(True)

    def rebuild_thumbs(self, clear_first):
        if clear_first:
            log_i("Clearing thumbanils dir..")
            GalleryDB.clear_thumb_dir()

        gs = []
        gs.extend(app_constants.GALLERY_DATA)
        gs.extend(app_constants.GALLERY_ADDITION_DATA)
        self.DATA_COUNT.emit(len(app_constants.GALLERY_DATA))
        log_i('Regenerating thumbnails')
        for n, g in enumerate(gs, 1):
            execute(GalleryDB.rebuild_thumb, False, g)
            g.reset_profile()
            self.PROGRESS.emit(n)
        self.DONE.emit(True)


class DatabaseStartup(QObject):
    """
    Fetches and emits database records
    START: emitted when fetching from DB occurs
    DONE: emitted when the initial fetching from DB finishes
    """
    START: pyqtBoundSignal = pyqtSignal()
    DONE: pyqtBoundSignal = pyqtSignal()
    PROGRESS: pyqtBoundSignal = pyqtSignal(str)
    _DB = DBBase

    def __init__(self):
        super().__init__()
        ListDB.init_lists()
        self._fetch_count = 500
        self._offset = 0
        self._fetching = False
        self.count = 0
        self._finished = False
        self._loaded_galleries = []

    def startup(self, manga_views):
        self.START.emit()
        self._fetching = True
        self.count = GalleryDB.gallery_count()
        remaining = self.count
        while remaining > 0:
            self.PROGRESS.emit("Loading galleries: {}".format(remaining))
            rec_to_fetch = min(remaining, self._fetch_count)
            self.fetch_galleries(self._offset, rec_to_fetch, manga_views)
            self._offset += rec_to_fetch
            remaining = self.count - self._offset
        [v.list_view.manga_delegate._increment_paint_level() for v in manga_views]
        self.PROGRESS.emit("Loading chapters...")
        self.fetch_chapters()
        self.PROGRESS.emit("Loading tags...")
        self.fetch_tags()
        [v.list_view.manga_delegate._increment_paint_level() for v in manga_views]
        self.PROGRESS.emit("Loading hashes...")
        self.fetch_hashes()
        self._fetching = False
        self.DONE.emit()

    def fetch_galleries(self, f, t, manga_views):
        c = execute(self._DB.execute, False, 'SELECT * FROM series LIMIT {}, {}'.format(f, t))
        if c:
            new_data = c.fetchall()
            gallery_list = execute(GalleryDB.gen_galleries, False, new_data,
                                   {"chapters": False, "tags": False, "hashes": False})
            # self._current_data.extend(gallery_list)
            if gallery_list:
                self._loaded_galleries.extend(gallery_list)
                for view in manga_views:
                    view_galleries = [g for g in gallery_list if g.view == view.view_type]
                    view.gallery_model._gallery_to_add = view_galleries
                    view.gallery_model.insertRows(view.gallery_model.rowCount(), len(view_galleries))

    def fetch_chapters(self):
        for g in self._loaded_galleries:
            g.chapters = execute(ChapterDB.get_chapters_for_gallery, False, g.id)

    def fetch_tags(self):
        for g in self._loaded_galleries:
            g.tags = execute(TagDB.get_gallery_tags, False, g.id)

    def fetch_hashes(self):
        for g in self._loaded_galleries:
            g.hashes = execute(HashDB.get_gallery_hashes, False, g.id)


if __name__ == '__main__':
    # unit testing here
    pass
