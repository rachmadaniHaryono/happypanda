"""test module."""
from itertools import product
from unittest import mock

import pytest

from happypanda.utils import IMG_FILES


@pytest.mark.parametrize(
    'ext',
    list(IMG_FILES) + [x.upper() for x in IMG_FILES] + [x.title() for x in IMG_FILES]
)
def test_find_filepath(ext):
    """test func."""
    path = mock.Mock()
    filename = 'file1.{}'.format(ext)
    scandir_res = mock.Mock()
    scandir_res.name = filename
    scandir_result = [scandir_res]
    with mock.patch('version.utils.scandir') as m_scandir, \
            mock.patch('version.utils.os') as m_os:
        m_scandir.scandir.return_value = scandir_result
        from version.utils import _find_filepath
        # run
        res = _find_filepath(path)
        # test
        m_scandir.scandir.assert_called_once_with(path)
        m_os.path.join.assert_called_once_with(path, filename)
        assert res == m_os.path.join.return_value


@pytest.mark.parametrize(
    'simple, gallery, exp_res', [
        # (gallery, exp_res),
        # namespace only, simple
        (True, {'namespace': []}, ''),
        (True, {'namespace': ['tag1', 'tag2']}, 'namespace,tag1, tag2'),
        (
            True,
            {'namespace1': ['tag1'], 'namespace2': ['tag2']},
            'namespace1,tag1, namespace2,tag2'), (
            True,
            {'namespace1': ['tag1', 'tag2'], 'namespace2':['tag3', 'tag4']},
            'namespace1,tag1, tag2, namespace2,tag3, tag4'
        ),
        # namespace only, not_simple
        (False, {'namespace': []}, ''),
        (False, {'namespace': ['tag1', 'tag2']}, 'namespace:[tag1, tag2]'),
        (
            False,
            {'namespace1': ['tag1'], 'namespace2': ['tag2']},
            'namespace1:tag1, namespace2:tag2'),
        (
            False,
            {'namespace1': ['tag1', 'tag2'], 'namespace2':['tag3', 'tag4']},
            'namespace1:[tag1, tag2], namespace2:[tag3, tag4]'
        ),
        # default only, simple
        (True, {'default': []}, ''),
        (True, {'default': ['tag1', 'tag2']}, 'tag1, tag2'),
        # default only, not_simple
        (False, {'default': []}, ''),
        (False, {'default': ['tag1', 'tag2']}, 'tag1, tag2'),
        # blank mix, simple
        (True, {'default': [], 'namespace': []}, ''),
        (True, {'default': ['tag1'], 'namespace': []}, 'tag1, '),
        (True, {'default': [], 'namespace': ['tag1']}, 'namespace,tag1'),
        # blank mix, not_simple
        (False, {'default': [], 'namespace': []}, ''),
        (False, {'default': ['tag1'], 'namespace': []}, 'tag1, '),
        (False, {'default': [], 'namespace': ['tag1']}, 'namespace:tag1'),
        # mix, simple
        (True, {'default': ['tag1'], 'namespace': ['tag2']}, 'tag1, namespace,tag2'),
        (
            True,
            {'default': ['tag1', 'tag2'], 'namespace':['tag3', 'tag4']},
            'tag1, tag2, namespace,tag3, tag4'
        ),
        # mix, not_simple
        (False, {'default': ['tag1'], 'namespace': ['tag2']}, 'tag1, namespace:tag2'),
        (
            False,
            {'default': ['tag1', 'tag2'], 'namespace':['tag3', 'tag4']},
            'tag1, tag2, namespace:[tag3, tag4]'
        ),
    ]
)
def test_tag_to_string(simple, gallery, exp_res):
    """test func."""
    from version.utils import tag_to_string
    res = tag_to_string(gallery, simple=simple)
    assert res == exp_res


@pytest.mark.parametrize(
    'tag_in_gallery, add_second_tag',
    product([False, True], repeat=2)
)
def test_get_gallery_tags(tag_in_gallery, add_second_tag):
    """test func."""
    tag = mock.Mock()
    tag2 = mock.Mock()
    tags = [tag]
    if add_second_tag:
        tags.append(tag2)
    namespace = mock.Mock()
    g_tags = {}
    if tag_in_gallery:
        g_tags[namespace] = [tag]
    else:
        g_tags[namespace] = []
    from version.utils import get_gallery_tags
    # run
    res = get_gallery_tags(tags, g_tags, namespace)
    # test
    if add_second_tag:
        assert res == {namespace: [tag, tag2]}
    else:
        assert res == {namespace: [tag]}


def test_cleanup_dir():
    """test func."""
    root = mock.Mock()
    m_dir = mock.Mock()
    dirs = [m_dir]
    m_file = mock.Mock()
    files = [m_file]
    path = mock.Mock()
    join_result = mock.Mock()
    with mock.patch('version.utils.os') as m_os, \
            mock.patch('version.utils.scandir') as m_sd:
        from version.utils import cleanup_dir
        m_sd.walk.return_value = [(root, dirs, files)]
        m_os.path.join.return_value = join_result
        # run
        cleanup_dir(path)
        # test
        m_sd.walk.assert_called_once_with(path, topdown=False)
        m_os.assert_has_calls([
            mock.call.path.join(root, m_file),
            mock.call.remove(join_result),
            mock.call.path.join(root, m_dir),
            mock.call.rmdir(join_result)
        ])


@pytest.mark.parametrize('key_in_list', [True, False])
def test_append_or_create_list_on_dict(key_in_list):
    """test func."""
    key = mock.Mock()
    value = mock.Mock()
    if key_in_list:
        dict_ = {key: []}
    else:
        dict_ = {}
    from version.utils import append_or_create_list_on_dict
    # run
    res = append_or_create_list_on_dict(dict_=dict_, key=key, value=value)
    # test
    assert res[key] == [value]


def test_get_chapter_pages_len():
    """test func."""
    valid_exts = ['.jpg', '.bmp', '.png', '.gif', '.jpeg']
    test_exts = valid_exts + ['.random_ext']
    scandir_result = []
    for ext in test_exts:
        m = mock.Mock()
        m.name = 'basename{}'.format(ext)
        scandir_result.append(m)
    exp_res = len(valid_exts)
    #
    chapter_path = mock.Mock()
    with mock.patch('version.utils.scandir') as m_sd:
        from version.utils import get_chapter_pages_len
        m_sd.scandir.return_value = scandir_result
        # run
        res = get_chapter_pages_len(chapter_path)
        # test
        assert res == exp_res
        m_sd.scandir.assert_called_once_with(chapter_path)


@pytest.mark.parametrize(
    'mode, value',
    product(['L', 'RGB', 'random'], product([0, 1], repeat=2))
)
def test_image_greyscale(mode, value):
    """test func."""
    filepath = mock.Mock()
    #
    idx0_val = mock.Mock()
    idx1_val = mock.Mock()
    idx2_val = mock.Mock()
    split_result = [idx0_val, idx1_val, idx2_val]
    #
    img = mock.Mock()
    img.mode = mode
    img.split.return_value = split_result
    #
    with mock.patch('version.utils.Image') as m_img, \
            mock.patch('version.utils.ImageChops') as m_ic:
        m_img.open.return_value.convert.return_value = img
        m_ic.difference.return_value.getextrema.side_effect = [
            (mock.Mock(), value[0]), (mock.Mock(), value[1])]
        from version.utils import image_greyscale
        # run
        res = image_greyscale(filepath=filepath)
        m_img.assert_has_calls([
            mock.call.open(filepath), mock.call.open().convert('RGB')])
        if mode not in ('L', 'RGB'):
            assert not res
            assert not m_ic.mock_calls
        elif mode == 'L':
            assert res
            assert not m_ic.mock_calls
        elif mode == 'RGB':
            img.split.assert_called_once_with()
            if value[0] != 0:
                m_ic.assert_has_calls([
                    mock.call.difference(idx0_val, idx1_val),
                    mock.call.difference().getextrema(),
                ])
            else:
                m_ic.assert_has_calls([
                    mock.call.difference(idx0_val, idx1_val),
                    mock.call.difference().getextrema(),
                    mock.call.difference(idx0_val, idx2_val),
                    mock.call.difference().getextrema()
                ])
            if any(x != 0 for x in value):
                assert not res
            else:
                assert res


def test_get_chapter_title():
    """test func."""
    split_path_part = mock.Mock()
    title = mock.Mock()
    path = mock.Mock()
    with mock.patch('version.utils.title_parser') as m_tp, \
            mock.patch('version.utils.os') as m_os:
        m_os.path.split.return_value = [mock.Mock(), split_path_part]
        m_tp.return_value = {'title': title}
        from version.utils import get_chapter_title
        # run
        res = get_chapter_title(path)
        # test
        m_tp.assert_called_once_with(split_path_part)
        m_os.path.split.assert_called_once_with(path)
        assert res == title


@pytest.mark.parametrize('is_dir_retval', [True, False])
def test_get_temp_path(is_dir_retval):
    """test function."""
    with mock.patch('version.utils.app_constants') as m_ac, \
            mock.patch('version.utils.uuid') as m_uuid, \
            mock.patch('version.utils.os') as m_os:
        from version.utils import _get_temp_path
        m_os.path.isdir.return_value = is_dir_retval
        res = _get_temp_path()
        os_calls = [
            mock.call.path.join(m_ac.temp_dir, str(m_uuid.uuid4.return_value)),
            mock.call.path.isdir(m_ac.temp_dir),
        ]
        if not is_dir_retval:
            os_calls.append(mock.call.mkdir(m_ac.temp_dir))
        os_calls.append(mock.call.mkdir(m_os.path.join.return_value))
        m_os.assert_has_calls(os_calls)
        assert m_os.path.join.return_value == res


@pytest.mark.parametrize(
    'os_name, select, raise_error',
    product(
        ['darwin', 'windows', 'linux', None],
        [None, '', mock.Mock()],
        [False, True]
    )
)
def test_open_path(os_name, select, raise_error):
    """test function."""
    path = mock.Mock()
    with mock.patch('version.utils.app_constants') as m_ac, \
            mock.patch('version.utils.subprocess') as m_sp, \
            mock.patch('version.utils.os') as m_os:
        if raise_error:
            m_sp.Popen.side_effect = lambda _: OSError()
            m_os.startfile.side_effect = lambda _: OSError()
        m_ac.OS_NAME = os_name
        from version.utils import open_path
        # run
        try:
            if select is None:
                open_path(path=path)
            else:
                open_path(path=path, select=select)
        except OSError as err:
            if raise_error:
                m_ac.NOTIF_BAR.add_text.assert_called_once_with(
                    'Could not open specified location. It might not exist anymore.')
                return
            else:
                raise err
        # test
        if os_name == 'darwin':
            m_sp.Popen.assert_called_once_with(['open', path])
        elif os_name == 'windows' and select:
            m_os.path.normcase.assert_called_once_with(select)
            m_sp.Popen.assert_called_once_with(
                r'explorer.exe /select,"{}"'.format(m_os.path.normcase.return_value), shell=True)
        elif os_name == 'windows':
            m_os.startfile.assert_called_once_with(path)
        elif os_name == 'linux':
            m_sp.Popen(('xdg-open', path))
        elif os_name not in ('darwin', 'windows', 'linux'):
            m_ac.NOTIF_BAR.add_text.assert_called_once_with(
                "I don't know how you've managed to do this.. "
                "If you see this, you're in deep trouble..."
            )


@pytest.mark.parametrize('isdir_retval', [True, False])
def test_makedirs_if_not_exists(isdir_retval):
    """test func."""
    folder = mock.Mock()
    with mock.patch('version.utils.os') as m_os:
        from version.utils import makedirs_if_not_exists
        m_os.path.isdir.return_value = isdir_retval
        makedirs_if_not_exists(folder)
        if not isdir_retval:
            m_os.makedirs.assert_called_once_with(folder)
        else:
            assert not m_os.makedirs.called


def test_backup_database():
    """test func."""
    today_datetime = '2016-12-28 19:28:24.199740'
    date = today_datetime.split(' ')[0]
    db_path = mock.Mock()
    base_path = mock.Mock()
    name = mock.Mock()
    with mock.patch('version.utils.datetime') as m_dt, \
            mock.patch('version.utils.os') as m_os, \
            mock.patch('version.utils.shutil') as m_shutil, \
            mock.patch('version.utils.makedirs_if_not_exists') as m_mine:
        m_dt.datetime.today.return_value = today_datetime
        m_os.path.split.return_value = (base_path, name)
        m_os.path.exists.return_value = False
        from version.utils import backup_database
        res = backup_database(db_path)
        # test
        assert res
        m_os.assert_has_calls([
            mock.call.path.split(db_path),
            mock.call.path.join(base_path, 'backup'),
            mock.call.path.join(
                m_os.path.join.return_value,
                "{}-{}".format(date, name)
            ),
            mock.call.path.exists(m_os.path.join.return_value)
        ])
        m_shutil.copyfile(db_path, m_os.path.join.return_value)
        m_mine.assert_called_once_with(m_os.path.join.return_value)


def test_get_date_age():
    """test func."""
    input_date = mock.Mock()
    with mock.patch('version.utils.PrettyDelta') as m_pd:
        from version.utils import get_date_age
        # run
        res = get_date_age(input_date)
        # test
        m_pd.assert_has_calls([
            mock.call(input_date),
            mock.call().format(),
        ])
        assert res == m_pd.return_value.format.return_value
