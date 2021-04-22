"""Top-level package for Orbit Viewer."""

__author__ = """Patrick Boettcher"""
__email__ = 'p@yai.se'
__version__ = '0.1.0'

from ._trajectories import Trajectories

trajectories = _trajectories.Trajectories()

from .orbit_viewer import OrbitViewer
