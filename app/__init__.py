from flask import Flask, Markup, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import argparse
import os
from pathlib import Path
import logging

app = Flask(__name__)

db = SQLAlchemy()


@app.before_first_request
# This is only run if the main() function isn't
# which is usually when "flask run" is used.
def on_start():
    # Cache the website's logo so it can be rendered directly into each page, to reduce loading time.
    with open(Path(app.static_folder) / "banner.svg", "r") as f:
        app.config["logoSvg"] = Markup(f.read())

    if (app.debug is False) or (
        "db_initialized" in app.config and app.config["db_initialized"] is True
    ):
        return
    app.config.from_object("app.config")
    with app.app_context():
        logging.info("Initializing DB through debug method")
        db.init_app(app)
        app.config["db_initialized"] = True
    migrate = Migrate(app, db, render_as_batch=True)
    db.create_all()

    from app import models, views


@app.context_processor
# Inject logo svg and alerts from session into template context.
def inject_logo_and_alert():
    d = dict(logo=app.config["logoSvg"])
    if "alert" in session:
        d["alert"] = session.pop("alert")

    return d


def main():
    parser = argparse.ArgumentParser(
        description="gymcorp-website",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-d", "--database", help="Path to app database", nargs="?")
    parser.add_argument(
        "--host", help="address to host site on.", default="0.0.0.0", type=str
    )
    parser.add_argument(
        "-p", "--port", help="port to host site on.", default=5000, type=int
    )
    parser.add_argument(
        "--populate", help="initialise database with default data.", action="store_true"
    )
    parser.add_argument(
        "--production", help="run with debug mode off.", action="store_true"
    )
    parser.add_argument(
        "--nossl",
        help="Run without SSL, to use with a reverse proxy or development.",
        action="store_true",
    )
    parser.add_argument("--ssl-cert", help="Path to SSL/TLS certificate to use.")
    parser.add_argument("--ssl-key", help="Path to SSL/TLS key file to use.")

    app.config.from_object("app.config")
    args = parser.parse_args()

    if args.database:
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "sqlite:///"
            + str(Path(args.database).resolve())
            + "?check_same_thread=False"
        )

    if "GYMCORP_DB_FILEPATH" in os.environ:
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "sqlite:///"
            + str(Path(os.environ["GYMCORP_DB_FILEPATH"]).resolve())
            + "?check_same_thread=False"
        )

    logging.info("Initializing DB through main method")
    db.init_app(app)
    app.config["db_initialized"] = True

    migrate = Migrate(app, db, render_as_batch=True)

    from app import models

    if args.populate or "GYMCORP_POPULATE" in os.environ:
        with app.app_context():
            db.create_all()
        from app.populate import populate

        with app.app_context():
            populate(
                makeBooking=False,
                wipeStripe=(not ("GYMCORP_POPULATE_NOSTRIPE" in os.environ)),
            )

    from app import views

    host = args.host
    if "GYMCORP_HOST" in os.environ:
        host = os.environ["GYMCORP_HOST"]
    port = args.port
    if "GYMCORP_PORT" in os.environ:
        port = int(os.environ["GYMCORP_PORT"])

    flaskArgs = {"debug": (not args.production), "host": host, "port": port}
    sslCert = "cert.pem"
    sslKey = "key.pem"
    if "GYMCORP_SSL_CERT" in os.environ:
        sslCert = os.environ["GYMCORP_SSL_CERT"]
    elif args.ssl_cert:
        sslCert = args.ssl_cert

    if "GYMCORP_SSL_KEY" in os.environ:
        sslKey = os.environ["GYMCORP_SSL_KEY"]
    elif args.ssl_key:
        sslKey = args.ssl_key

    keyFilesExist = False
    if Path(sslCert).exists() and Path(sslKey).exists():
        keyFilesExist = True
    elif not (args.nossl or "GYMCORP_NOSSL" in os.environ):
        logging.warning("SSL/TLS Certificate/Key not found, running without HTTPS.")

    if keyFilesExist and not (args.nossl or "GYMCORP_NOSSL" in os.environ):
        flaskArgs["ssl_context"] = (sslCert, sslKey)

    app.run(**flaskArgs)
