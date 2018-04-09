.. _getting_started:

Getting Started
===============

.. todo::

    - Add directions to sample project files.
    - Provide suggested instructions for setting up sample project
    - Provide suggested instructions running the model

Project Configuration
=====================

.. todo::

    - Provide outline of basic folder structure

Inputs
^^^^^^

Data on a number of key inputs are required for the model to function.

Premises
^^^^^^^^

Premises are the most granular layer the model utilises. Data should ideally consist of a set of premises points with indicators for the number of residential or non-residential premises at that particular location. Coordinates for these points, and also the postcode they are attached to, are useful attributes.

.. csv-table:: Premises input data
   :header: "Premise_ID", "Residential", "Non_Residential", "Latitude", "Longitude", Dist_Point_ID, "Postcode"
   :widths: 10, 10, 10, 10, 10, 10, 10

   premise_1, 0, 1, 52.205304, 0.11661316, dist_point_1, CB2 1TN
   premise_2, 0, 1, 52.200671, 0.11371496, dist_point_5, CB3 9EU

Distribution Points
^^^^^^^^^^^^^^^^^^^

Distribution points serve a very limited number of premises and are either hung aerially or exist in a buried manhole. Each distribution point usually serves approximately 8 premises.

.. csv-table:: Distribution point input data
   :header: "Dist_Point_ID", "Latitude", "Longitude", "Cabinet_ID"
   :widths: 10, 10, 10, 10

   dist_point_1, 52.205304, 0.11661316, cabinet_1
   dist_point_2, 52.205304, 0.11661316, cabinet_1

Cabinets
^^^^^^^^

A cabinet exists as a green box, often on a street corner, and holds active equipment (such as a VDSL2 DSLAM).
Cabinets serve up to approximately 500 premises.

.. csv-table:: Cabinets input data
   :header: "Cabinet_ID", "Latitude", "Longitude", "Exchange_ID"
   :widths: 10, 10, 10, 10

   cabinet_1, 52.205304, 0.11661316, "exchange_1"
   cabinet_2, 52.205304, 0.11661316, "exchange_1"

Exchanges
^^^^^^^^^

Exchanges are also know as 'Central Offices', and contain the Main Distribution Frame (ADSL) and Optical Fibre Distribution Frame (FTTx)

.. csv-table:: Exchanges input data
   :header: "Exchange_ID", "Latitude", "Longitude",
   :widths: 10, 10, 10, 10

   exchange_1, 52.205304, 0.11661316
   exchange_2, 52.205304, 0.11661316
