from app import app
from app.models import *        # noqa: F403,F401
from app.controllers import *   # noqa: F403,F401
"""
The last 2 imports are needed to connect the
controller routes to the app instance.
However, flake8 does not detect the use of
these imports, resulting in warnings.
noqa tells flake8 to ignore the specific codes
for only these 2 lines.
"""


"""
This file runs the server on port 8081
"""

FLASK_PORT = 8081

if __name__ == "__main__":
    app.run(debug=True, port=FLASK_PORT, host='0.0.0.0')
