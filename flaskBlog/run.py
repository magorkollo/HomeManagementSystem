from flaskblog import app
import threading

import flaskblog


if __name__ == "__main__":
    # t = threading.Thread(target=flaskblog.routes.detect_motion)
    # t.daemon = True
    # t.start()
    app.run(debug = True, threaded=True, host="0.0.0.0")