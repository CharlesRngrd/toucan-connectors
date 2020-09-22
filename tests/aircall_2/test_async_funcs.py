"""Module containing tests with fake server."""

import pytest

import tests.general_helpers as helpers
from tests.aircall.helpers import assert_called_with
from toucan_connectors.aircall_2.aircall_2_connector import AircallError, fetch_page

fetch_fn_name = 'toucan_connectors.aircall_2.aircall_2_connector.fetch'


async def test_fetch_page_with_no_next(mocker):
    """It should return an array of one response."""
    dataset = 'tags'
    fake_data = {'data': {'stuff': 'stuff'}, 'meta': {'next_page_link': None, 'current_page': 1}}
    fake_data = helpers.build_future(fake_data)
    fake_fetch = mocker.patch(fetch_fn_name, return_value=fake_data)
    result = await fetch_page(dataset, [], {}, 10, 0)
    assert len(result) == 1
    first_dict = result[0]
    assert 'data' in first_dict
    assert 'meta' in first_dict

    assert_called_with(fake_fetch, ['https://api.aircall.io/v1/tags?per_page=50&page=1', {}])


async def test_fetch_page_with_next_page(mocker):
    """It should return multiple pages."""
    dataset = 'calls'
    data_list = [
        {
            'data': {'stuff': 'stuff'},
            'meta': {'next_page_link': '/calls?page=2', 'current_page': 1},
        },
        {'data': {'stuff': 'stuff'}, 'meta': {'next_page_link': None, 'current_page': 2}},
    ]
    data_list = [helpers.build_future(item) for item in data_list]
    fake_fetch = mocker.patch(fetch_fn_name, side_effect=data_list)

    # limit is 10 and run is 0 i.e. this is the first run
    # want to see that, despite the limit being set to 10,
    # only two objects are sent in the array because no next_page_link
    # on second object means that there is no more to be fetched
    fake_res = await fetch_page(dataset, [], {}, 10, 0)
    assert len(fake_res) == 2

    assert_called_with(fake_fetch, ['https://api.aircall.io/v1/calls?per_page=50&page=2', {}], 2)


async def test_fetch_page_with_low_limit(mocker):
    """It should stop recursion due to limit"""
    dataset = 'users'
    data_list = [
        {
            'data': {'stuff': 'stuff'},
            'meta': {'next_page_link': '/users?page=2', 'current_page': 1},
        },
        {
            'data': {'stuff': 'stuff'},
            'meta': {'next_page_link': '/users?page=3', 'current_page': 2},
        },
        {'data': {'stuff': 'stuff'}, 'meta': {'next_page_link': None, 'current_page': 3}},
    ]
    data_list = [helpers.build_future(item) for item in data_list]
    fake_fetch = mocker.patch(fetch_fn_name, side_effect=data_list)
    # limit is only 1 and run is 0 i.e. this is the first run
    res = await fetch_page(dataset, [], {}, 1, 0)
    assert len(res) == 1

    assert_called_with(fake_fetch, ['https://api.aircall.io/v1/users?per_page=50&page=1', {}])


async def test_fetch_page_with_no_meta(mocker):
    """Tests that no meta object in response is not an issue"""
    dataset = 'calls'
    fake_data = {'data': {'stuff': 'stuff'}}
    fake_data = helpers.build_future(fake_data)
    fake_fetch = mocker.patch(fetch_fn_name, return_value=fake_data)
    # despite there being a limit of 10 runs, only one run should occur
    res = await fetch_page(dataset, [], {}, 10, 0)
    assert len(res) == 1
    assert_called_with(fake_fetch, expected_count=1)


async def test_fetch_page_with_error(mocker):
    """
    Tests error sent from API goes through a retry policy and then throws an exception
    """
    dataset = 'tags'
    fake_data = {'error': 'Oops!', 'troubleshoot': 'Blah blah blah'}
    fake_data = helpers.build_future(fake_data)
    fake_fetch = mocker.patch(fetch_fn_name, return_value=fake_data)
    with pytest.raises(AircallError) as e:
        await fetch_page(dataset, [], {}, 1, 0)
    fake_fetch.call_count == 4
    assert str(e.value) == 'Aborting Aircall requests due to Oops!'
