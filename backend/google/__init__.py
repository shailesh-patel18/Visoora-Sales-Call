# Google namespace package — allows coexistence with google.protobuf
# Uses implicit namespace packages (PEP 420) via pkgutil extension
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
