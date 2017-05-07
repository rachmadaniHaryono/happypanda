"""test main module."""
from unittest import mock



def assert_argparse(mock_argparse):
    """assertion for arg parsing."""
    from version.main import parse_args
    mock_argparse.assert_has_calls([
        mock.call.ArgumentParser(
            description='A manga/doujinshi manager with tagging support', prog='Happypanda'),
        mock.call.ArgumentParser().add_argument(
            '-d', '--debug', action='store_true',
            help='happypanda_debug_log.log will be created in main directory'),
        mock.call.ArgumentParser().add_argument(
            '-t', '--test', action='store_true',
            help='Run happypanda in test mode. 5000 gallery will be preadded in DB.'),
        mock.call.ArgumentParser().add_argument(
            '-v', '--version', action='version', version='Happypanda v0.30'),
        mock.call.ArgumentParser().add_argument(
            '-e', '--exceptions', action='store_true', help='Disable custom excepthook'),
        mock.call.ArgumentParser().add_argument(
            '-x', '--dev', action='store_true', help='Development Switch'),
        mock.call.ArgumentParser().parse_args(),
    ], any_order=True)


def test_parse_args():
    """test parse_args."""
    from version.main import parse_args
    with mock.patch('version.main.argparse') as mock_argparse:
        res = parse_args()
        assert len(mock_argparse.mock_calls) == 7
        res == mock_argparse.ArgumentParser.return_value.parse_args.return_value
        assert_argparse(mock_argparse)
