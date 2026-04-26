from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("applire")
except PackageNotFoundError:
    __version__ = "unknown"
