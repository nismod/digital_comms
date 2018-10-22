The Cambridge Communications Assessment Model
=============================================

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](http://ccam.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/nismod/digital_comms.svg?branch=master)](https://travis-ci.org/nismod/digital_comms)
[![Coverage Status](https://coveralls.io/repos/github/nismod/digital_comms/badge.svg?branch=master)](https://coveralls.io/github/nismod/digital_comms?branch=master)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1468787.svg)](https://doi.org/10.5281/zenodo.1468787)

Description
===========
The **Cambridge Communications Assessment Model** (ccam) is a decision support tool to quantify the performance of national digital infrastructure strategies. 

## Citation:
```
Oughton, E. J. and Frias, Z. (2017) The cost, coverage and rollout implications of 5G infrastructure 
in Britain. Telecommunications Policy. doi: 10.1016/j.telpol.2017.07.009.
```

Setup and configuration
=======================

All code for **The Cambridge Communications Assessment Model** is written in 
Python (Python>=3.6) and has a number of dependencies. 
See requirements.txt for a full list.

Using conda
-----------

The recommended installation method is to use `conda<http://www.conda.pydata.org/miniconda.html>`_, 
which handles packages and virtual environments, along with the conda-forge channel which has 
a host of pre-built libraries and packages.

Create a conda environment, using 'digital_comms' as a short reference for digital communications:

    conda create --name digital_comms python=3.6

Activate it:

    activate digital_comms

For development purposes:

Run this command once per machine:

    python setup.py develop

Windows users may need to additionally install Shapely as follows:

    conda install shapely

To install ccam permanently:

    python setup.py install

To build the documentation:

    python setup.py docs

Users may need to additionally install Sphinx as follows:

    conda install sphinx

And potentially recommonmark: 

    pip install recommonmark

The run the tests:

    python setup.py test

Background and funding 
==========================

The **Cambridge Communications Assessment Model** has been collaboratively developed between the [Networks and Operating Systems Group (NetOS)](http://www.cl.cam.ac.uk/research/srg/netos) at the [Cambridge Computer Laboratory](http://www.cl.cam.ac.uk), the [Environmental Change Institute](http://www.eci.ox.ac.uk/) at the [University of Oxford](https://www.ox.ac.uk/), and the UK's [Digital Catapult](http://www.digtalcatapult.org.uk). Research activity between 2017-2018 also partially took place at the [Cambridge Judge Business School](http://www.jbs.cam.ac.uk/home/) at the [University of Cambridge](http://www.cam.ac.uk/). 

Development has been funded by the EPSRC via (i) the [Infrastructure Transitions Research Consortium](http://www.itrc.org.uk/) (EP/N017064/1) and (ii) the UK's [Digital Catapult](http://www.digitalcatapult.org.uk)

