# The Cambridge Communications Assessment Model

**The Cambridge Communications Assessment Model** currently focuses on 
the mobile sector to provide analytics for 
decision-makers on (i) capacity-demand and (ii) risk, vulnerability 
and resilience. The fixed, wireless and satellite sectors are currently under development. 

## Setup and Configuration

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
