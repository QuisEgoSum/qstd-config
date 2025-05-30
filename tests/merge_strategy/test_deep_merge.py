from qstd_config.merge_strategy import DeepMergeStrategy


def test_deep_merge():
    merge_strategy = DeepMergeStrategy()

    base = {
        'a': 1,
        'b': {
            'a': 1,
            'b': {
                'a': 1,
                'c': 1,
            },
            'c': 1,
        },
        'c': 1,
    }
    override = {
        'a': 2,
        'b': {
            'a': 2,
            'b': {
                'a': 2,
                'd': 2,
            },
        },
        'd': 2,
    }

    merged = merge_strategy.merge(base, override)

    assert merged == {
        'a': 2,
        'b': {
            'a': 2,
            'b': {
                'a': 2,
                'c': 1,
                'd': 2,
            },
            'c': 1,
        },
        'c': 1,
        'd': 2,
    }
