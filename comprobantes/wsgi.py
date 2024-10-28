import sys

from GeneradorComprobantes import app

if __name__ == "__main__":
    sys.argv.append("--timeout")
    sys.argv.append('300')
    app.run()