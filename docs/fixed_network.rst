.. _fixed_network:

==================
Data preprocessing
==================

The fixed_network data pre-processing pipeline reads raw data on the fixed broadband network in the UK, appends this with data for areas where data is not available and transforms this into a set of shapefiles that can be interpetated by the fixed_network model.

File structure
--------------

- ``data/digital_comms/raw`` 
    Contains an archive of untouched incoming data 
- ``data/digital_comms/intermediate`` 
    Contains intermediate files, necessary to enable preprocessing data on a cluster
- ``data/digital_comms/processed`` 
    Contains the final result that can be read by the fixed_network model

Preprocessing
----------------

**Local machine option**

*Step 1*

Generate exchange areas, this is necessary to split up the problem in ~5895 units, to be run in a distributed environment. Note that this is a memory extensive process that should be run on a high-memory machine ~120GB of RAM required.

``python scripts/network_cluster_input_files.py``

If you have no access to such a machine, you can also get the ``intermediate/exchange_areas`` folder from a previous job (on the cluster) and put it in you local project.

*Step 2*

Run pre-processing per exchange area, make sure to give the exchange area as an argument to the script.

``python scripts/network_preprocess_input_files.py exchange_EACAM``

This generate an intermediate file per exchange_area in ``processed/exchange_EACAM``

**Cluster option**

This single script generates `intermediate/exchange_areas` on the host node and then distributes pre-processing jobs over the cluster using *GNU_parallel*. The exchange areas are not re-generated if they already exist, delete them if you will need to regenerate these.

``cd scripts``

``run_parallel.sh``

Results collection
------------------

Collect the intermediate results and process this into a single results set in the ``processed`` directory. Without arguments the script will collect all the areas that are present in the ``intermediate`` folder. With an argument, it will collect data for a certain subset, for example Cambridge, Oxford, Leeds and Newcastle.

``python scripts/network_preprocess_collect_results.py``
``python scripts/network_preprocess_collect_results.py Cambridge``