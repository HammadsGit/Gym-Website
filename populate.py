# Populates the database with initial values from the brief.
import sys
from app.populate import populate
from app import app, db

app.config.from_object("app.config")
# db.init_app(app)
populate(makeBooking=("booking" in sys.argv[len(sys.argv) - 1]))
