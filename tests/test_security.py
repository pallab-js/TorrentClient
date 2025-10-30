from utils.security import sanitize_path


def test_sanitize_path_allows_inside(tmp_path):
    base = tmp_path / 'base'
    base.mkdir()
    safe = sanitize_path(str(base), 'subdir/file.txt')
    assert safe and str(base) in safe


def test_sanitize_path_blocks_escape(tmp_path):
    base = tmp_path / 'base'
    base.mkdir()
    unsafe = sanitize_path(str(base), '../escape')
    assert unsafe is None
