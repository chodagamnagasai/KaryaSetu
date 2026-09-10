# Lightweight syntax/import tests are intentionally kept independent of MongoDB.
def test_source_exists():
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath('backend','server.py').exists()
