#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import pytest
from pytest import fixture
from shapely.geometry import Point, LineString
import os
from collections import OrderedDict
from digital_comms.mobile_network.model import NetworkManager

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

@fixture(scope='function')
def setup_postcode_sector():
    return {
        'type': 'Feature', 'id': '1045',
        'properties': OrderedDict([('SectID', 1046), ('RMSect', 'CB1 1'),
            ('GISSect', 'CB 1 1'), ('StrSect', 'CB11'), ('PostDist', 'CB1'),
            ('PostArea', 'CB'), ('DistNum', '1'), ('SecNum', 1), ('PCCnt', 107),
            ('AnomCnt', 0), ('RefPC', 'CB11DP'), ('x', 545708),
            ('y', 258524), ('Sprawl', 'Cambridge'), ('Locale', None)]),
        'geometry': {
            'type': 'Polygon', 'coordinates': [[(545081.0927873488, 258778.53467021856),
            (545148.2158297729, 258767.60779800318), (545182.0947858373, 258794.72003720546),
            (545266.80454359, 258787.9419774049), (545331.1819806674, 258726.94943633815),
            (545382.0127823557, 258747.28361573984), (545466.7225401084, 258750.66264850178),
            (545514.156376623, 258706.61525693646), (545568.3758984238, 258730.33846623843),
            (545615.8097349384, 258764.2187681029), (545622.5871751636, 258689.6801045734),
            (545737.7954139293, 258693.06913447368), (545734.4066938167, 258784.55294750462),
            (545995.3134072999, 258794.72003720546), (546046.1359639271, 258760.82973820262),
            (546169.7706551381, 258808.59606523375), (546168.294789201, 258805.63691228247),
            (546177.9415106893, 258791.5609414872), (546204.8039197567, 258752.39215343614),
            (546196.0971352339, 258746.24391335156), (546195.1489532073, 258741.2053556237),
            (546193.9781545309, 258699.76721716745), (546151.9613231597, 258680.0528603434),
            (546147.6161759595, 258676.5838533363), (546143.007186804, 258672.99488066908),
            (546139.9812493798, 258669.00602246786), (546139.0495574754, 258667.97631721792),
            (546132.9647023828, 258661.00831178873), (546125.9976257524, 258647.00232096188),
            (546124.9834832369, 258641.96376323403), (546123.9775857825, 258632.0266077152),
            (546126.9870330845, 258632.0066134385), (546133.9788448982, 258628.98747765715),
            (546141.0118820175, 258626.96805571066), (546147.9954487701, 258622.049463643),
            (546156.9825653703, 258611.96235104895), (546160.9814200043, 258605.96406803958),
            (546164.955539455, 258598.956074057), (546167.0168047303, 258594.0074905743),
            (546167.9484966347, 258590.02862951142), (546167.9979670014, 258586.0197770335),
            (546179.4256216874, 258588.1391703635), (546188.9486672592, 258589.9786438197),
            (546191.9333793778, 258574.373110857), (546191.9498695, 258574.0432052915),
            (546196.0064395618, 258550.0100847007), (546195.9981945007, 258548.00065989257),
            (546198.958171436, 258544.97152697286), (546200.9699663447, 258544.03179596807),
            (546205.001801223, 258544.04179310641), (546206.9888609485, 258543.9818102763),
            (546207.7144263254, 258544.09177879815), (546205.3893190948, 258499.92442157265),
            (546164.7329228054, 258466.04411970818), (546113.902121117, 258445.7099403065),
            (546086.7923602166, 258496.53539167237), (546080.0231650526, 258564.30599253965),
            (546069.8570047149, 258632.07659340696), (546046.1359639271, 258649.01174577003),
            (546029.1923633643, 258608.353384105), (546042.7472438145, 258560.91696263937),
            (546035.9698035894, 258516.86957107406), (546015.6374829141, 258462.6550898079),
            (546019.0262030266, 258333.89194787387), (546007.8706353569, 258258.6234932449),
            (546007.0955996134, 258258.83343315023), (545995.6267196217, 258262.72231996796),
            (545991.405248338, 258264.38184493387), (545988.0907337753, 258265.6114929508),
            (545987.2167572987, 258264.9216904047), (545981.6266058721, 258260.69290088312),
            (545903.8262093221, 258320.3458254111), (545886.8826087593, 258184.8046236765),
            (545822.505171682, 258117.0340228092), (545758.1194895435, 258052.66244898055),
            (545703.9082128038, 257906.95415754511), (545641.8393928347, 257940.38458818386),
            (545624.1537367728, 257904.24493305254), (545641.1385626411, 257876.092991462),
            (545583.637506522, 257817.11987234175), (545516.6381400145, 257787.49835141393),
            (545514.156376623, 257791.7471352122), (545514.156376623, 257862.90676597977),
            (545559.0342441963, 257939.45485431742), (545571.7646185365, 257961.16863881127),
            (545564.9871783113, 258032.32826957884), (545405.7338231435, 258198.36074327762),
            (545372.2753651952, 258206.88830228924), (545382.0127823557, 258215.29589564068),
            (545246.4804679758, 258374.5503095389), (545192.5165430692, 258362.29381792314),
            (545078.5615535908, 258550.58991872496), (545053.9088208985, 258594.67729884366),
            (545044.3692852046, 258589.23885558185), (545043.1737513449, 258591.40823460356),
            (545005.9060751679, 258649.01174577003), (545043.1737513449, 258669.3459251717),
            (545090.6075878595, 258689.67010743506), (545081.0927873488, 258778.53467021856)]]
            }}


@fixture(scope='function')
def setup_lad():
    return [
        {
            "id": 1,
            "name": "Cambridge",
        }
    ]

@fixture(scope='function')
def setup_pcd_sector():
    return [
        {
            "id": "CB11",
            "lad_id": 1,
            "population": 500,
            "area": 2,
            "user_throughput": 2,
        },
        {
            "id": "CB12",
            "lad_id": 1,
            "population": 200,
            "area": 2,
            "user_throughput": 2,
        }
    ]

@fixture(scope='function')
def setup_assets():
    return [
        {
            "pcd_sector": "CB11",
            "site_ngr": "site_100",
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800", "2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017,
            "sectors": 3,
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": "site_200",
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800", "2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017,
            "sectors": 3,
        }
    ]

@fixture(scope='function')
def setup_six_sectored_assets():
    return [
        {
            "pcd_sector": "CB11",
            "site_ngr": "site_100",
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800", "2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017,
            "sectors": 6,
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": "site_200",
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800", "2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017,
            "sectors": 6,
        }
    ]

@fixture(scope='function')
def setup_site_sectors():
    return 3

@fixture(scope='function')
def setup_capacity_lookup():
    return {
        ("Urban", "700", "2x10MHz", 30): [
            (0, 0),
            (1, 2),
        ],
        ("Urban", "800", "2x10MHz", 30): [
            (0, 0),
            (1, 2),
        ],
        ("Urban", "2600", "2x10MHz", 30): [
            (0, 0),
            (3, 5),
        ],
        ("Urban", "3500", "2x10MHz", 30): [
            (0, 0),
            (3, 5),
        ],
        ('Small cells', '3700', '2x25MHz', 30): [
            (0, 0),
            (3, 10),
        ],
        ("Rural", "700", "2x10MHz", 30): [
            (0, 0),
            (1, 2),
        ],
        ("Rural", "800", "2x10MHz", 30): [
            (0, 0),
            (1, 2),
            (2, 4),
        ],
        ("Rural", "2600", "2x10MHz", 30): [
            (0, 0),
            (2, 4),
            (3, 5),
        ],
        ("Rural", "3500", "2x10MHz", 30): [
            (0, 0),
            (3, 5),
        ],
        ("Rural", "1800", "2x10MHz", 30): [
            (0, 0),
            (0, 0),
        ],
        ("Urban", "700", "2x10MHz", 40): [
            (0, 0),
            (2, 4),
        ],
        ("Urban", "800", "2x10MHz", 40): [
            (0, 0),
            (2, 4),
        ],
        ("Urban", "2600", "2x10MHz", 40): [
            (0, 0),
            (6, 10),
        ],
        ("Urban", "3500", "2x10MHz", 40): [
            (0, 0),
            (6, 10),
        ],
        ('Small cells', '3700', '2x25MHz', 40): [
            (0, 0),
            (6, 20),
        ],
        ("Rural", "700", "2x10MHz", 40): [
            (0, 0),
            (2, 4),
        ],
        ("Rural", "800", "2x10MHz", 40): [
            (0, 0),
            (2, 4),
        ],
        ("Rural", "2600", "2x10MHz", 40): [
            (0, 0),
            (6, 10),
        ],
        ("Rural", "3500", "2x10MHz", 40): [
            (0, 0),
            (6, 10),
        ],
        ("Rural", "1800", "2x10MHz", 40): [
            (0, 0),
            (0, 0),
        ],
    }

@fixture(scope='function')
def setup_clutter_lookup():
    return  [
        (0.0, 'Rural'),
        (782.0, 'Suburban'),
        (7959.0, 'Urban'),
    ]

@fixture(scope='function')
def setup_service_obligation_capacity():
    return 2

@fixture(scope='function')
def setup_traffic():
    return 0.15

@fixture(scope='function')
def setup_market_share():
    return 0.25

@fixture(scope='function')
def setup_mast_height():
    return 30

@fixture(scope='function')
def setup_built_interventions():
    return [
        {
            "pcd_sector": "CB11",
            "site_ngr": 100,
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800"],
            "bandwidth": "2x10MHz",
            "build_date": 2017
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": 200,
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017
        }
    ]

@fixture(scope='function')
def setup_interventions():
    return {
    'upgrade_to_lte': {
        'name': 'Upgrade site to LTE',
        'description': 'If a site has only 2G/3G',
        'result': '800 and 2600 bands available',
        'cost': 142446,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '2600',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'carrier_700': {
        'name': 'Build 700 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '700 band available',
        'cost': 50917,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '700',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'carrier_3500': {
        'name': 'Build 3500 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '3500 band available',
        'cost': 50917,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '3500',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'sectorisation': {
        'name': 'sectorisation carrier',
        'description': 'Available if a site has LTE',
        'result': '6 sectors are available',
        'cost': 50000, #£10k each, plus £20 installation
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': 'x6_sectors',
                'technology': 'same',
                'type': 'macrocell_site',
                'bandwidth': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'build_macro_site': {
        'name': 'Build a new macro site',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': 'Macrocell sites available at given density',
        'cost': 150000,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'new_macro_site',
                'frequency': 'same',
                'technology': 'same',
                'type': 'macro_site',
                'bandwidth': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'small_cell': {
        'name': 'Build a small cell',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': '2x25 MHz small cells available at given density',
        'cost': 40220,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'small_cell_sites',
                'frequency': '3700',
                'technology': '5G',
                'type': 'small_cell',
                'bandwidth': '2x25MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'raise_mast_height': {
        'name': 'Raises existing mast height',
        'description': 'Must be deployed at preset densities to \
            be modelled',
        'result': 'Same technology but with new enhanced capacity',
        'cost': 30000,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'extended_height',
                'frequency': 'same',
                'technology': 'same',
                'type': 'extended_height_macro',
                'bandwidth': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'deploy_c_ran': {
        'name': 'Replace D-Ran with C-RAN',
        'description': 'Must be deployed within viable distance \
            from exchange',
        'result': 'Network architecture change to SDN/NFV',
        'cost': 30000,
        'assets_to_build': [
            {
                'site_ngr': 'c_ran',
                'frequency': 'same',
                'technology': '5G c_ran',
                'type': 'macro_c_ran',
                'bandwidth': 'same',
                'build_date': None,
            },
        ]
    },
}

@fixture(scope='function')
def setup_strategies():
    return {
    'minimal': (),
    'macrocell_700_3500': (
        'upgrade_to_lte', 'carrier_700', 'carrier_3500'
        ),
    'macrocell_700': ('upgrade_to_lte', 'carrier_700'),
    'sectorisation': (
        'upgrade_to_lte', 'carrier_700',
        'carrier_3500', 'x6_sectors'
        ),
    'macro_densification': ('build_macro_site'),
    'deregulation': ('raise_mast_height'),
    'cloud_ran': ('deploy_c_ran'),
    'small_cell': ('upgrade_to_lte', 'small_cell'),
    'small_cell_and_spectrum': (
        'upgrade_to_lte', 'carrier_700',
        'carrier_3500', 'small_cell'
        ),
    }






@fixture(scope='function')
def setup_fixed_model_pcp():
    return [
        ((-1.944580, 52.792175), {'Name': 'cab_1', 'Type': 'pcp'}),
        ((-0.395508, 52.485498), {'Name': 'cab_2', 'Type': 'pcp'}),
        ((-2.713623, 52.652437), {'Name': 'cab_3', 'Type': 'pcp'}),
        (( 0.417480, 51.147694), {'Name': 'cab_4', 'Type': 'pcp'}),
        (( 1.219482, 52.431944), {'Name': 'cab_5', 'Type': 'pcp'}),
        ((-1.900635, 51.223443), {'Name': 'cab_6', 'Type': 'pcp'}),
        (( 0.802002, 51.154586), {'Name': 'cab_7', 'Type': 'pcp'})
    ]

@fixture(scope='function')
def setup_fixed_model_exchanges():
    return [
        ((-0.572275, 51.704581), {'Name': 'EAARR', 'Type': 'exchange'}),
        (( 0.537344, 51.745323), {'Name': 'EABTM', 'Type': 'exchange'})
    ]

@fixture(scope='function')
def setup_fixed_model_corenodes():
    return [
        ((0.3, 51.825323), {'Name': 'CoreNode', 'Type': 'core'})
    ]

@fixture(scope='function')
def setup_fixed_model_links():
    return [
        ([(-0.572275, 51.704581), (0, 52), (-1.944580, 52.792175)], {'Origin': 'EAARR',    'Dest': 'cab_1', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([(-0.572275, 51.704581), (0, 52), (-0.395508, 52.485498)], {'Origin': 'EAARR',    'Dest': 'cab_2', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([(-0.572275, 51.704581), (0, 52), (-2.713623, 52.652437)], {'Origin': 'EAARR',    'Dest': 'cab_3', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([(-0.572275, 51.704581), (0, 52), ( 0.417480, 51.147694)], {'Origin': 'EAARR',    'Dest': 'cab_4', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([( 0.537344, 51.745323), (0, 52), ( 1.219482, 52.431944)], {'Origin': 'EABTM',    'Dest': 'cab_5', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.537344, 51.745323), (0, 52), (-1.900635, 51.223443)], {'Origin': 'EABTM',    'Dest': 'cab_6', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.537344, 51.745323), (0, 52), ( 0.802002, 51.154586)], {'Origin': 'EABTM',    'Dest': 'cab_7', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.3,      51.825323), (0, 51), (-0.572275, 51.704581)], {'Origin': 'CoreNode', 'Dest': 'EAARR', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.3,      51.825323), (0, 51), ( 0.537344, 51.745323)], {'Origin': 'CoreNode', 'Dest': 'EABTM', 'Type': 'link', 'Physical': 'copper'    })
    ]

@fixture(scope='function')
def setup_fixed_network(setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):
    empty_data = {}

    return NetworkManager(empty_data, empty_data, setup_fixed_model_pcp,
                      setup_fixed_model_exchanges, empty_data,
                      setup_fixed_model_links)
