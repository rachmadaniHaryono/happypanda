"""test module."""
from unittest import mock

import pytest


@pytest.mark.parametrize(
    'c_dt_arg, day_reduction, exp_res',
    [[(2016, 12, 28), 27, {
        'day': 27, 'hour': 0.0, 'minute': 0.0, 'month': 0.9, 'second': 0,
        'year': 0.07397260273972603
    }]]
)
def test_init(c_dt_arg, day_reduction, exp_res):
    """test init."""
    import datetime
    current_datetime = datetime.datetime(*c_dt_arg)
    input_date = datetime.datetime.fromordinal(
        current_datetime.toordinal() - day_reduction)
    with mock.patch('version.pretty_delta.datetime') as m_dt:
        m_dt.datetime.now.return_value = current_datetime
        from version.pretty_delta import PrettyDelta
        # run
        obj = PrettyDelta(input_date)
        # test
        for key in exp_res:
            assert getattr(obj, key) == pytest.approx(exp_res[key])


@pytest.mark.parametrize(
    'c_dt_arg, day_reduction, exp_res',
    [[(2016, 12, 28), 27, '27 days']]
)
def test_format(c_dt_arg, day_reduction, exp_res):
    """test  method."""
    import datetime
    current_datetime = datetime.datetime(*c_dt_arg)
    input_date = datetime.datetime.fromordinal(
        current_datetime.toordinal() - day_reduction)
    with mock.patch('version.pretty_delta.datetime') as m_dt:
        m_dt.datetime.now.return_value = current_datetime
        from version.pretty_delta import PrettyDelta
        # run
        obj = PrettyDelta(input_date)
        # test
        assert obj.format() == exp_res


@pytest.mark.parametrize('a, b, exp_res', [[27, 365, (0.07397260273972603, 27)]])
def test_q_n_r(a, b, exp_res):
    """test method."""
    from version.pretty_delta import PrettyDelta
    res = PrettyDelta.q_n_r(a=a, b=b)
    assert pytest.approx(exp_res[0]) == res[0]
    assert exp_res[1] == res[1]


@pytest.mark.parametrize(
    'n, s, exp_res',
    [
        (1, 'text', '1 text'),
        (2, 'text', '2 texts'),
    ]
)
def test_formatn(n, s, exp_res):
    """test method."""
    from version.pretty_delta import PrettyDelta
    res = PrettyDelta.formatn(n=n, s=s)
    assert res == exp_res
