"""Top-level package for Orbit Viewer."""

__author__ = """Patrick Boettcher"""
__email__ = 'p@yai.se'
__version__ = '0.1.0'

from . import _trajectories

trajectories = _trajectories.Trajectories()
