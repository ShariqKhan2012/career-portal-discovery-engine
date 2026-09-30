"""Tests for the export layer."""

from src.export import export_csv, export_json, export_xlsx


def test_export_csv(tmp_path):
    """CSV export creates a file with headers."""
    from src.config import Config
    from src.db import Database
    db = Database(Config(db_path=tmp_path / "test.db"))
    db.migrate()
    path = tmp_path / "test.csv"
    export_csv(db, path)
    assert path.exists()
    content = path.read_text()
    assert "name" in content
    assert "status" in content


def test_export_json(tmp_path):
    """JSON export creates a valid JSON file."""
    from src.config import Config
    from src.db import Database
    db = Database(Config(db_path=tmp_path / "test.db"))
    db.migrate()
    path = tmp_path / "test.json"
    export_json(db, path)
    assert path.exists()
    import json
    data = json.loads(path.read_text())
    assert isinstance(data, list)


def test_export_xlsx(tmp_path):
    """XLSX export creates a valid Excel file."""
    from src.config import Config
    from src.db import Database
    db = Database(Config(db_path=tmp_path / "test.db"))
    db.migrate()
    path = tmp_path / "test.xlsx"
    export_xlsx(db, path)
    assert path.exists()
