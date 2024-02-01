from pathlib import Path

WTF_CSRF_ENABLED = True
SECRET_KEY = "1BCDEFGHIJKLMNOPQRSTUVWXYZ12345"


basedir = Path(__file__).parent.parent.resolve()
SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(basedir / "app.db?check_same_thread=False")
SQLALCHEMY_TRACK_MODIFICATIONS = True
