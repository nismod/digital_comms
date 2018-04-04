The Cambridge Communications Assessment Model
=============================================

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](http://ccam.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/nismod/digital_comms.svg?branch=master)](https://travis-ci.org/nismod/digital_comms)
[![Coverage Status](https://coveralls.io/repos/github/nismod/digital_comms/badge.svg?branch=master)](https://coveralls.io/github/nismod/digital_comms?branch=master)

*(click on the 'docs' button to get directed to the full model documentation)*

Description
===========
**The Cambridge Communications Assessment Model** provides analytics for 
decision-makers on (i) capacity-demand and (ii) risk, vulnerability and 
resilience. The fixed, wireless and satellite sectors are currently under development. 

## Citation:
```
Oughton, E. J. and Frias, Z. (2017) The cost, coverage and rollout implications of 5G infrastructure 
in Britain. Telecommunications Policy. doi: 10.1016/j.telpol.2017.07.009.
```

Setup and configuration
=======================

All code for **The Cambridge Communications Assessment Model** is written in 
Python (Python>=3.5) and has a number of dependencies. 
See requirements.txt for a full list.

Using conda
-----------

The recommended installation method is to use `conda<http://conda.pydata.org/miniconda.html>`_, 
which handles packages and virtual environments, along with the conda-forge channel which has 
a host of pre-built libraries and packages.

Create a conda environment, using 'digital_comms' as a short reference for digital communications:

    conda create --name digital_comms python=3.6

Activate it:

    activate digital_comms

For development purposes:

Run this command once per machine:

    python setup.py develop

To install permanently:

    python setup.py install

To build the documentation:

    python setup.py docs

The run the tests:

    python setup.py test

Funding (EPSRC Grant EP/N017064/1)
==========================

**The Cambridge Communications Assessment Model** was written and 
developed at the [Judge Business School](http://www.jbs.cam.ac.uk/home/), 
[University of Cambridge](http://www.cam.ac.uk/) and at the [Environmental Change Institute](http://www.eci.ox.ac.uk/), 
[University of Oxford](https://www.ox.ac.uk/) within the EPSRC-sponsored MISTRAL programme, 
as part of the [Infrastructure Transition Research Consortium](http://www.itrc.org.uk/).

