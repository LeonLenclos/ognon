"""
Ognon is a a local-only web application for the creation of 2D animation.
Run `python -m ognon` to start the server. Then browse http://lacalhost:40460
"""
import os

__version__ = '1.α'
HTTP_ADRESS = ('localhost', 40460)
OSC_ADRESS = ('localhost', 50460)
PROJECTS_DIR = os.path.expanduser('~/ognons/')

print(os.path.join(os.path.dirname(__file__), 'tests'))

from . import model
from . import server
from . import view
from . import cursor
from . import projects
from . import tags
from . import utils
from . import control
