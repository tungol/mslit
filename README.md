mslit and reduce.py
===================

This is software designed to streamline the process of reduction of multiple
split spectroscopic images. The images are of the type described in _Multi-slits
at Kitt Peak: A Manual for Designing and Using Entrance Masks for 
Low/Moderate-Resolution Spectroscopy_ by De Veny et al., published 1996 by Kitt
Peak National Observatory.

Requirements
------------

* Python 2.5+
* PyRAF <http://www.stsci.edu/institute/software_hardware/pyraf>
* PyFITS <http://www.stsci.edu/institute/software_hardware/pyfits/>
* SciPy and NumPy <http://www.scipy.org/>
* PyYAML <http://pyyaml.org/wiki/PyYAML>
* argparse <https://code.google.com/p/argparse/> (already included in Python 2.7)

The final, analysis functionality requires two additional modules:

* matplotlib <http://matplotlib.sourceforge.net/>
* coords <https://trac.assembla.com/astrolib>

Usage
-----

For usage information, see USAGE.txt.