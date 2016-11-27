"""test module."""
from itertools import product
from unittest import mock

import pytest

from version.utils import IMG_FILES


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
