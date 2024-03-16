import updator
from waitress import serve
from codebase import app, port


if __name__ == '__main__':
    updator.init_system()
    serve(app, host="0.0.0.0", port=port)