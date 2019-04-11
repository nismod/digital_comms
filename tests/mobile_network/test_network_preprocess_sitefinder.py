import pytest
import os

from scripts.network_preprocess_sitefinder import process_asset_data

"""
Test for scripts/network_preprocess_sitefinder.py.

Written by Edward Oughton, 1st April 2019.

"""

@pytest.fixture
def load_data():

    assets = [
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545955.226499999989755, 258485.065899999986868]
        },
        'properties':{
            'operator': 'Orange',
            'Opref': 'CAM0119',
            'Sitengr': 'TL4584058530',
            'Antennaht': 16,
            'Transtype': 'GSM',
            'Freqband': '1800',
            'Anttype': 'SECTOR',
            'Powerdbw': 29.5,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545955.226499999989755, 258485.065899999986868]
        },
        'properties':{
            'operator': 'Orange',
            'Opref': 'CAM0119',
            'Sitengr': 'TL4584058530',
            'Antennaht': 16,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'SECTOR',
            'Powerdbw': 27.2,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'Three',
            'Opref': 'CB0387',
            'Sitengr': 'TL4584458536',
            'Antennaht': 15.4,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'Sectored',
            'Powerdbw': 25.8,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'T-Mobile',
            'Opref': '91064',
            'Sitengr': 'TL4584458536',
            'Antennaht': 17.8,
            'Transtype': 'GSM',
            'Freqband': '1800',
            'Anttype': 'SECTOR',
            'Powerdbw': 26,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'T-Mobile',
            'Opref': '91064',
            'Sitengr': 'TL4584458536',
            'Antennaht': 17.8,
            'Transtype': 'GSM',
            'Freqband': '1800',
            'Anttype': 'SECTOR',
            'Powerdbw': 26,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'T-Mobile',
            'Opref': '91064',
            'Sitengr': 'TL4584458536',
            'Antennaht': 17.8,
            'Transtype': 'GSM',
            'Freqband': '1800',
            'Anttype': 'SECTOR',
            'Powerdbw': 26,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'T-Mobile',
            'Opref': '91064',
            'Sitengr': 'TL4584458536',
            'Antennaht': 14.5,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'SECTOR',
            'Powerdbw': 19,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
           }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'T-Mobile',
            'Opref': '91064',
            'Sitengr': 'TL4584458536',
            'Antennaht': 16.1,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'SECTOR',
            'Powerdbw': 18,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'T-Mobile',
            'Opref': '91064',
            'Sitengr': 'TL4584458536',
            'Antennaht': 16.1,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'SECTOR',
            'Powerdbw': 18,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'Voda',
            'Opref': '46497',
            'Sitengr': 'TL4584458536',
            'Antennaht': 13.7,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'Macro',
            'Powerdbw': 28.1,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'Voda',
            'Opref': '46497',
            'Sitengr': 'TL4584458536',
            'Antennaht': 15.3,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'Macro',
            'Powerdbw': 28.1,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545959.220899999956600, 258491.082800000003772]
        },
        'properties':{
            'operator': 'Voda',
            'Opref': '46497',
            'Sitengr': 'TL4584458536',
            'Antennaht': 13.7,
            'Transtype': 'UMTS',
            'Freqband': '2100',
            'Anttype': 'Macro',
            'Powerdbw': 28.1,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': '',
            }
        },
        ]

    return assets

def test_process_asset_data(load_data):

    actual_processed_data = process_asset_data(load_data)

    expected_processed_data = [
        {
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [545957.2237, 258488.07434999995],
            },
        'properties':{
            'Antennaht': 16.0,
            'Transtype': ['GSM','UMTS','UMTS','GSM','GSM','GSM','UMTS',
                'UMTS','UMTS','UMTS','UMTS','UMTS'],
            'Freqband': ['1800','2100','2100','1800','1800','1800','2100',
                '2100','2100','2100','2100','2100'],
            'Anttype': ['SECTOR','SECTOR','Sectored','SECTOR','SECTOR',
                'SECTOR','SECTOR','SECTOR','SECTOR','Macro','Macro','Macro'],
            'Powerdbw': 22.166666666666668,
            'Maxpwrdbw': 32,
            'Maxpwrdbm': 0,
            }
        }
        ]

    assert len(actual_processed_data) == len(expected_processed_data)
    assert actual_processed_data == expected_processed_data
