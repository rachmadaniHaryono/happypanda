"""archive file."""
import os
import logging
import zipfile
import uuid
import rarfile

try:
    import app_constants
except ImportError:
    from . import app_constants

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


class ArchiveFile():
    """Work with archive files, raises exception if instance fails.

    namelist -> returns a list with all files in archive
    extract <- Extracts one specific file to given path
    open -> open the given file in archive, returns bytes
    close -> close archive
    """

    zip, rar = range(2)

    @classmethod
    def _check_archive(cls, filepath):
        """check_archive.

        Returns:
            return True file is bad.
        """
        archive_files_1part = ARCHIVE_FILES[:2]
        archive_files_2part = ARCHIVE_FILES[2:]
        b_f = True
        if filepath.endswith(ARCHIVE_FILES) and filepath.endswith(archive_files_1part):
            cls.archive = zipfile.ZipFile(os.path.normcase(filepath))
            b_f = cls.archive.testzip()
            cls.type = cls.zip
        elif filepath.endswith(ARCHIVE_FILES) and filepath.endswith(archive_files_2part):
            cls.archive = rarfile.RarFile(os.path.normcase(filepath))
            b_f = cls.archive.testrar()
            cls.type = cls.rar
        return b_f

    def __init__(self, filepath):
        """__init__."""
        self.type = 0
        try:
            # check for bad file.
            b_f = self._check_archive(filepath=filepath)
            if filepath.endswith(ARCHIVE_FILES):
                # test for corruption
                if b_f:
                    log_w('Bad file found in archive {}'.format(
                        filepath.encode(errors='ignore')))
                    raise app_constants.CreateArchiveFail
            else:
                log_e('Archive: Unsupported file format')
                raise app_constants.CreateArchiveFail
        except:
            log.exception('Create archive: FAIL')
            raise app_constants.CreateArchiveFail

    def namelist(self):
        """namelist."""
        filelist = self.archive.namelist()
        return filelist

    def is_dir(self, name):
        """is_dir.

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

    def dir_list(self, only_top_level=False):
        """Return a list of all directories found recursively.

        For directories not in toplevel
        a path in the archive to the diretory will be returned.
        """
        if only_top_level:
            if self.type == self.zip:
                return [x for x in self.namelist() if x.endswith('/') and x.count('/') == 1]
            elif self.type == self.rar:
                potential_dirs = [
                    x for x in self.namelist() if x.count('/') == 0]
                return [
                    x.filename for x in [
                        self.archive.getinfo(y)
                        for y in potential_dirs
                    ] if x.isdir()
                ]
        else:
            if self.type == self.zip:
                return [x for x in self.namelist() if x.endswith('/') and x.count('/') >= 1]
            elif self.type == self.rar:
                return [x.filename for x in self.archive.infolist() if x.isdir()]

    def dir_contents(self, dir_name):
        """Return a list of contents in the directory.

        An empty string will return the contents of the top folder
        """
        if dir_name and dir_name not in self.namelist():
            log_e('Directory {} not found in archive'.format(dir_name))
            raise app_constants.FileNotFoundInArchive
        if not dir_name:
            if self.type == self.zip:
                con = [x for x in self.namelist() if x.count('/') == 0 or
                       (x.count('/') == 1 and x.endswith('/'))]
            elif self.type == self.rar:
                con = [x for x in self.namelist() if x.count('/') == 0]
            return con
        if self.type == self.zip:
            dir_con_start = [
                x for x in self.namelist() if x.startswith(dir_name)]
            return [x for x in dir_con_start if x.count('/') == dir_name.count('/') or
                    (x.count('/') == 1 + dir_name.count('/') and x.endswith('/'))]
        elif self.type == self.rar:
            return [x for x in self.namelist() if x.startswith(dir_name) and
                    x.count('/') == 1 + dir_name.count('/')]
        return []

    @staticmethod
    def _make_temp_dir(path=None):
        """create temp dir if specified."""
        if not path:
            path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
            os.mkdir(path)
        return path

    def extract(self, file_to_ext, path=None):
        """Extract one file from archive to given path.

        Creates a temp_dir if path is not specified
        Returns path to the extracted file
        """
        path = self._make_temp_dir(path=path)
        #
        if not file_to_ext:
            return self.extract_all(path)
        else:
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
        """Extract all files to given path, and returns path.

        If path is not specified, a temp dir will be created
        """
        path = self._make_temp_dir(path=path)
        #
        if member:
            self.archive.extractall(path, member)
        self.archive.extractall(path)
        return path

    def open(self, file_to_open, fp=False):
        """Return bytes. If fp set to true, returns file-like object."""
        if fp:
            return self.archive.open(file_to_open)
        else:
            return self.archive.open(file_to_open).read()

    def close(self):
        """close."""
        self.archive.close()
