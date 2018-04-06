# The Cambridge Communications Assessment Model
[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](http://ccam.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/nismod/digital_comms.svg?branch=master)](https://travis-ci.org/nismod/digital_comms)
[![Coverage Status](https://coveralls.io/repos/github/nismod/digital_comms/badge.svg?branch=master)](https://coveralls.io/github/nismod/digital_comms?branch=master)

*(click on the 'docs' button to get directed to the full model documentation)*

**The Cambridge Communications Assessment Model** currently focuses on
the mobile sector to provide analytics for
decision-makers on (i) capacity-demand and (ii) risk, vulnerability
and resilience. The fixed, wireless and satellite sectors are currently under development.

## Citation:
```
Oughton, E. J. and Frias, Z. (2017) 'The cost, coverage and rollout implications of 5G infrastructure in Britain'.
Telecommunications Policy. doi: 10.1016/j.telpol.2017.07.009.

```

## Setup and configuration

All code is written in Python (Python>=3.5), avoiding external dependencies.

## A word from our sponsors

**The Cambridge Communications Assessment Model** was written and
developed at the [Judge Business School](http://www.jbs.cam.ac.uk/home/),
[University of Cambridge](http://www.cam.ac.uk/) and at the [Environmental Change Institute](http://www.eci.ox.ac.uk/),
[University of Oxford](https://www.ox.ac.uk/) within the EPSRC-sponsored MISTRAL programme,
as part of the [Infrastructure Transition Research Consortium](http://www.itrc.org.uk/).

## Install

For development purposes:

Run this command once per machine:

        python setup.py develop

To install permanently:

        python setup.py install

To build the documentation:

        python setup.py docs

The docs are available in html format in `/docs/_build/html/index.html`

The run the tests:

        python setup.py test
