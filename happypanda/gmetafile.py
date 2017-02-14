"""gmetafile."""
import datetime
import logging
import scandir
import json

try:
    import app_constants
    import utils
    from archive_file import ArchiveFile
except ImportError:
    from . import app_constants
    from . import utils
    from .archive_file import ArchiveFile

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class GMetafile:
    """gmetafile."""

    def __init__(self, path=None, archive=''):
        """init func."""
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
            zip = ArchiveFile(archive)
            c = zip.dir_contents(path)
            for x in c:
                if x.endswith(app_constants.GALLERY_METAFILE_KEYWORDS):
                    self.files.append(open(zip.extract(x), encoding='utf-8'))
        else:
            for p in scandir.scandir(path):
                if p.name in app_constants.GALLERY_METAFILE_KEYWORDS:
                    self.files.append(open(p.path, encoding='utf-8'))
        if self.files:
            self.detect()
        else:
            log_d('No metafile found...')

    def _eze(self, fp):
        if not fp.name.endswith('.json'):
            return
        j = json.load(fp, encoding='utf-8')
        eze = ['gallery_info', 'image_api_key', 'image_info']
        # eze
        if all(x in j for x in eze):
            log_i('Detected metafile: eze')
            ezedata = j['gallery_info']
            t_parser = utils.title_parser(ezedata['title'])
            self.metadata['title'] = t_parser['title']
            self.metadata['type'] = ezedata['category']
            for ns in ezedata['tags']:
                self.metadata['tags'][ns.capitalize()] = ezedata['tags'][ns]
            self.metadata['tags']['default'] = self.metadata[
                'tags'].pop('Misc', [])
            self.metadata['artist'] = self.metadata['tags']['Artist'][0].capitalize()\
                if 'Artist' in self.metadata['tags'] else t_parser['artist']
            self.metadata['language'] = ezedata['language']
            d = ezedata['upload_date']
            # should be zero padded
            d[3] = d[1] = int("0" + str(d[1])) if len(str(d[1])) == 1 else d[1]
            self.metadata['pub_date'] = datetime.datetime.strptime(
                "{} {} {}".format(d[0], d[1], d[3]), "%Y %m %d")
            l = ezedata['source']
            self.metadata['link'] = 'http://' + l['site'] + \
                '.org/g/' + str(l['gid']) + '/' + l['token']
            return True

    def _hdoujindler(self, fp):  # NOQA
        """HDoujin Downloader."""
        if not fp.name.endswith('info.txt'):
            return
        lines = fp.readlines()
        if lines:
            for line in lines:
                splitted = line.split(':')
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
                        self.metadata['tags'].update(utils.tag_to_dict(other))
                    if "description" == l:
                        self.metadata['info'] = other
                    if "circle" in l:
                        if "group" not in self.metadata['tags']:
                            self.metadata['tags']['group'] = []
                            self.metadata['tags']['group'].append(
                                other.strip().lower())

            return True

    def detect(self):
        """detect."""
        for fp in self.files:
            with fp:
                z = False
                for x in [self._eze, self._hdoujindler]:
                    if x(fp):
                        z = True
                        break
                if not z:
                    log_i('Incompatible metafiles found')

    def update(self, other):
        """update."""
        self.metadata.update((x, y) for x, y in other.metadata.items() if y)

    def apply_gallery(self, gallery):
        """apply_gallery."""
        log_i('Applying metafile to gallery')
        if self.metadata['title']:
            gallery.title = self.metadata['title']
        if self.metadata['artist']:
            gallery.artist = self.metadata['artist']
        if self.metadata['type']:
            gallery.type = self.metadata['type']
        if self.metadata['tags']:
            gallery.tags = self.metadata['tags']
        if self.metadata['language']:
            gallery.language = self.metadata['language']
        if self.metadata['pub_date']:
            gallery.pub_date = self.metadata['pub_date']
        if self.metadata['link']:
            gallery.link = self.metadata['link']
        if self.metadata['info']:
            gallery.info = self.metadata['info']
        return gallery
