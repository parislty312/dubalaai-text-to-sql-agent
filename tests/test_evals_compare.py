from src.evals import multiset_equal


def test_equal_simple():
    assert multiset_equal([("Rock", 826.65)], [("Rock", 826.65)])


def test_order_insensitive():
    assert multiset_equal([(1,), (2,)], [(2,), (1,)])


def test_float_rounding():
    assert multiset_equal([("a", 826.6501)], [("a", 826.65)])


def test_column_names_ignored_but_arity_matters():
    assert not multiset_equal([(1, 2)], [(1,)])


def test_duplicates_counted():
    assert not multiset_equal([(1,), (1,)], [(1,)])


def test_none_values_ok():
    assert multiset_equal([(None, "x")], [(None, "x")])


def test_empty_equals_empty():
    assert multiset_equal([], [])
