from app import create_app, db
from app.models import User, Post, Telescope, Galaxy, Event, Match

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Telescope': Telescope, 'Galaxy': Galaxy, 'Event': Event, 'Match': Match}
