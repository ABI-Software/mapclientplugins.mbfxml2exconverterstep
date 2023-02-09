
"""
MAP Client Plugin
"""

__version__ = '0.1.3'
__author__ = 'Hugh Sorby'
__stepname__ = 'mbfxml2exconverter'
__location__ = 'https://github.com/ABI-Software/mbfxml2exconverterstep.git'

# import class that derives itself from the step mountpoint.
from mapclientplugins.mbfxml2exconverterstep import step

# Import the resource file when the module is loaded,
# this enables the framework to use the step icon.
from . import resources_rc
