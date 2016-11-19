"""import export data."""
import logging
import os
import json
import datetime

try:
    import app_constants
    import gallerydb
except ImportError:
    from . import (
        app_constants,
        gallerydb,
    )

log = logging.getLogger(__name__)
""":class:`logging.Logger`: Logger for module."""
log_i = log.info
""":meth:`logging.Logger.info`: Info logger func"""
log_d = log.debug
""":meth:`logging.Logger.debug`: Debug logger func"""
log_w = log.warning
""":meth:`logging.Logger.warning`: Warning logger func"""
log_e = log.error
""":meth:`logging.Logger.error`: Error logger func"""
log_c = log.critical
""":meth:`logging.Logger.critical`: Critical logger func"""


class ImportExportData:
    """import exported data.

    Args:
        format(int):Format code.
    Attributes:
        structure:Structure.
        hash_pages_count(int):Hash of page count.
    """

    def __init__(self, format=1):
        """init func."""
        self.type = format
        if format == 0:
            self.structure = ""
        else:
            self.structure = {}
        self.hash_pages_count = 4

    def get_pages(self, pages):
        """Return pages to generate hashes from."""
        p = []
        if pages < self.hash_pages_count + 1:
            for x in range(pages):
                p.append(x)
        else:
            x = 0
            i = pages // self.hash_pages_count
            for t in range(self.hash_pages_count):
                x += i
                p.append(x - 1)
        return p

    def add_data(self, name, data):
        """add data.

        Args:
            name(str):Name.
            data:Data.
        """
        if self.type == 0:
            pass
        else:
            self.structure[name] = data

    def save(self, file_path):
        """"save data."""
        file_name = os.path.join(
            file_path, 'happypanda-{}.hpdb'.format(
                datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            )
        )
        with open(file_name, 'w', encoding='utf-8') as fp:
            json.dump(self.structure, fp, indent=4)

    def _find_pair_for_single_gallery(self, g, found_pairs, identifier):
        """find pair for single gallery.

        Args:
            g:Gallery.
            found_pairs:Founded pairs.
            identifier:Indentifier.
        Returns:
            founded pair.
        """
        found = None
        #
        pages = self.get_pages(g.chapters[0].pages)
        hashes = gallerydb.HashDB.gen_gallery_hash(g, 0, pages)
        for p in hashes:
            if hashes[p] != identifier[str(p)]:
                break
        else:
            found = g
            g.title = self.structure['title']
            g.artist = self.structure['artist']
            if self.structure['pub_date'] and self.structure['pub_date'] != 'None':
                g.pub_date = datetime.datetime.strptime(
                    self.structure['pub_date'], "%Y-%m-%d %H:%M:%S")
            g.type = self.structure['type']
            g.status = self.structure['status']
            if self.structure['last_read'] and self.structure['last_read'] != 'None':
                g.last_read = datetime.datetime.strptime(
                    self.structure['last_read'], "%Y-%m-%d %H:%M:%S")
            g.times_read += self.structure['times_read']
            g._db_v = self.structure['db_v']
            g.language = self.structure['language']
            g.link = self.structure['link']
            for ns in self.structure['tags']:
                if ns not in g.tags:
                    g.tags[ns] = []
                for tag in self.structure['tags'][ns]:
                    if tag not in g.tags[ns]:
                        g.tags[ns].append(tag)
            g.exed = self.structure['exed']
            g.info = self.structure['info']
            g.fav = self.structure['fav']
            gallerydb.GalleryDB.modify_gallery(
                g.id,
                g.title,
                artist=g.artist,
                info=g.info,
                type=g.type,
                fav=g.fav,
                tags=g.tags,
                language=g.language,
                status=g.status,
                pub_date=g.pub_date,
                link=g.link,
                times_read=g.times_read,
                _db_v=g._db_v,
                exed=g.exed
            )
        return found

    def find_pair(self, found_pairs):
        """find_pair.

        Args:
            found_pairs:Founded pair.
        Returns:
            found:Found pair.
        """
        identifier = self.structure['identifier']
        for g in app_constants.GALLERY_DATA:
            if g not in found_pairs and g.chapters[0].pages == identifier['pages']:
                found = self._find_pair_for_single_gallery(
                    g, found_pairs, identifier)
            if found:
                break
        return found
