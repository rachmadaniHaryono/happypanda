"""archive file."""
import os
import logging
import zipfile
import uuid
import rarfile

try:
    import app_constants
    from app_constants import ARCHIVE_FILES
except ImportError:
    from . import app_constants
    from .app_constants import ARCHIVE_FILES

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

# for rarfile.
rarfile.PATH_SEP = '/'
rarfile.UNRAR_TOOL = app_constants.unrar_tool_path


class ArchiveFile():
    """Work with archive files, raises exception if instance fails.

    Args:
        filepath: Filepath of archive file.
    """

    zip, rar = range(2)

    def _check_archive(self, filepath):
        """check_archive.

        Args:
            filepath: Filepath to check.

        Returns:
            return True file is bad.
        """
        archive_files_1part = ARCHIVE_FILES[:2]
        archive_files_2part = ARCHIVE_FILES[2:]
        b_f = True  # assume it is bad file
        if filepath.endswith(ARCHIVE_FILES) and filepath.endswith(archive_files_1part):
            self.archive = zipfile.ZipFile(os.path.normcase(filepath))
            b_f = self.archive.testzip()
            self.type = self.zip
        elif filepath.endswith(ARCHIVE_FILES) and filepath.endswith(archive_files_2part):
            self.archive = rarfile.RarFile(os.path.normcase(filepath))
            b_f = self.archive.testrar()
            self.type = self.rar
        return b_f

    def __init__(self, filepath):
        """init."""
        self.type = 0
        try:
            # check for bad file.
            is_bad_file = self._check_archive(filepath=filepath)
            # test for corruption
            if filepath.endswith(ARCHIVE_FILES) and not is_bad_file:
                # check archive result pass
                pass
            elif filepath.endswith(ARCHIVE_FILES) and is_bad_file:
                log_w('Bad file found in archive {}'.format(
                    filepath.encode(errors='ignore')
                ))
                raise app_constants.CreateArchiveFail
            else:
                log_e('Archive: Unsupported file format')
                raise app_constants.CreateArchiveFail
        except:
            log.exception('Create archive: FAIL')
            raise app_constants.CreateArchiveFail

    def namelist(self):
        """Returns a list with all files in archive.

        Returns:
            list: List of all files in archive.
        """
        filelist = self.archive.namelist()
        return filelist

    def is_dir(self, name):
        """Checks if the provided name in the archive is a directory or not

        Args:
            name: Name to check.

        Returns:
            bool: Returns True if name is a directory in archive.
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

        Args:
            only_top_level (bool): Return only top level or not.

        Returns:
            list: all directories and recursively if asked.
        """
        if only_top_level:
            if self.type == self.zip:
                return [x for x in self.namelist() if x.endswith('/') and x.count('/') == 1]
            elif self.type == self.rar:
                potential_dirs = [x for x in self.namelist() if x.count('/') == 0]
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

        Args:
            dir_name: Directory name.

        Returns:
            list: Directory contents.
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
        """create temp dir if specified.

        Args:
            path: Path for tempdir.

        Returns:
            Path of temporary directory.
        """
        if not path:
            path = os.path.join(app_constants.temp_dir, str(uuid.uuid4()))
            os.mkdir(path)
        return path

    def extract(self, file_to_ext, path=None):
        """Extract one specific file from archive to given path.

        Creates a temp_dir if path is not specified

        Args:
            file_to_ext: File to extract.
            path: Path for file to be extracted.

        Returns:
            Path to the extracted file
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

        Args:
            path: Optional path for extracted files.
            member: Member from archive.

        Returns:
            Path of extracted files.
        """
        path = self._make_temp_dir(path=path)
        #
        if member:
            self.archive.extractall(path, member)
        self.archive.extractall(path)
        return path

    def open(self, file_to_open, fp=False):
        """Open the given file in archive, returns bytes.

        Args:
            file_to_open: File to open.
            fp (bool): Determine return type.

        Return:
            Bytes if fp set to false, else returns file-like object
        """
        archive_fp = self.archive.open(file_to_open)
        if fp:
            return archive_fp
        else:
            return archive_fp.read()

    def close(self):
        """Close the archive."""
        self.archive.close()
