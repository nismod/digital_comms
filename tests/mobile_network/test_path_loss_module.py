import pytest
from digital_comms.mobile_network.path_loss_module import (
    path_loss_calculator,
    determine_path_loss,
    free_space,
    extended_hata,
    e_utra_3gpp_tr36_814,
    check_applicability
    )

#prepare for testing Free Space model
@pytest.mark.parametrize("frequency, distance, ant_height, ue_height, \
    expected", [
    (0.8,1000,20,1.5,93), #stochastic component is 3 (seed=42)
    (0.8,2000,20,1.5,99), #stochastic component is 3 (seed=42)
    (0.8,3000,20,1.5,103), #stochastic component is 3 (seed=42)
    (0.8,4000,20,1.5,106), #stochastic component is 3 (seed=42)
    (0.8,5000,20,1.5,107), #stochastic component is 3 (seed=42)
    (1.8,1000,20,1.5,101), #stochastic component is 3 (seed=42)
    (1.8,2000,20,1.5,107), #stochastic component is 3 (seed=42)
    (1.8,3000,20,1.5,110), #stochastic component is 3 (seed=42)
    (1.8,4000,20,1.5,113), #stochastic component is 3 (seed=42)
    (1.8,5000,20,1.5,114), #stochastic component is 3 (seed=42)
    (2.6,1000,20,1.5,104), #stochastic component is 3 (seed=42)
    (2.6,2000,20,1.5,110), #stochastic component is 3 (seed=42)
    (2.6,3000,20,1.5,113), #stochastic component is 3 (seed=42)
    (2.6,4000,20,1.5,116), #stochastic component is 3 (seed=42)
    (2.6,5000,20,1.5,118), #stochastic component is 3 (seed=42)
    ])

def test_free_space(frequency, distance, ant_height, ue_height, expected):
    assert (
        free_space(frequency, distance, ant_height, ue_height)
        ) == expected

#prepare for testing Extended HATA model
@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, \
    building_height, street_width, settlement_type, type_of_sight, \
    ue_height, above_roof, expected", [
    ####urban####
    # test distance <0.04 km, stochastic component = 6
    (0.8,20,20,'macro',20,20,'urban','los',1.5,1, 100),
    # test distance <0.04 km, above roof, stochastic component = 388
    (0.1,200,20,'macro',20,20,'urban','los',1.5,1, 505),
    # test distance >0.04 km, below roof, stochastic component = 4648
    (0.1,200,20,'',20,20,'urban','nlos',1.5,0, 4765),
    # test distance >0.04 km, above roof, stochastic component = 338
    (0.8,200,20,'',20,20,'urban','los',1.5,1, 557),
    # test distance >0.04 km, below roof, stochastic component = 4648
    (0.8,200,20,'',20,20,'urban','nlos',1.5,0, 4817),
    # test distance >0.04 km, above roof, stochastic component = 338
    (1.8,200,20,'',20,20,'urban','los',1.5,1, 613),
    # test distance >0.04 km, below roof, stochastic component = 4648
    (1.8,200,20,'',20,20,'urban','nlos',1.5,0, 4873),
    # test distance >0.04 km, above roof, stochastic component = 338
    (2.1,200,20,'',20,20,'urban','los',1.5,1, 617),
    # test distance >0.04 km, below roof, stochastic component = 4648
    # spreadsheet gives 4878 due to rounding.
    (2.1,200,20,'',20,20,'urban','nlos',1.5,0, 4877),
    ####suburban####
    # test distance >0.04 km, above roof, stochastic component = 338
    (0.8,200,20,'',20,20,'suburban','los',1.5,1, 529),
    # test distance >0.04 km, below roof, stochastic component = 4648
    (0.8,200,20,'',20,20,'suburban','nlos',1.5,0, 4789),
    # test distance 0.5 km, above roof, stochastic component = 112
    (0.8,500,20,'',20,20,'suburban','los',1.5,1, 274),
    # test distance 0.5 km, above roof, stochastic component = 184
    (0.8,500,20,'',20,20,'suburban','los',1.5,0, 346),
    ####rural####
    # test distance >0.04 km, above roof, stochastic component = 338
    (1.8,200,20,'',20,20,'rural','los',1.5,1, 441),
    #####test 500m####
    # test distance 0.05 km, above roof, stochastic component = 112
    (1.8,500,20,'',20,20,'urban','los',1.5,1, 357),
    # test distance 0.05 km, below roof, stochastic component =
    (1.8,500,20,'',20,20,'urban','nlos',1.5,0, 429), 
    #change distances
    #test 90m (0.04< d <0.1)
    # test distance 0.09 km, above roof, stochastic component = 47
    (1.8,90,20,'',20,20,'urban','los',1.5,1, 188),
    # test distance 0.09 km, below roof, stochastic component = 162
    (1.8,90,20,'',20,20,'urban','nlos',1.5,0, 297),
    #test 5km
    # test distance 5 km, above roof, stochastic component = 388
    (1.8,5000,20,'',20,20,'rural','los',1.5,1, 513),
    #test 25km
    # test distance 25 km, above roof, stochastic component = 388
    (0.7,25000,20,'',20,20,'rural','los',1.5,1, 537),
    # test distance 25 km, above roof, stochastic component = 388
    (0.7,25000,20,'',20,20,'rural','los',1.5,1, 537),
    #test 50km
    # test distance 50 km, above roof, stochastic component = 388
    (0.7,50000,20,'',20,20,'rural','los',1.5,1, 553),
    ])

def test_extended_hata(frequency, distance, ant_height, ant_type, 
    building_height, street_width, settlement_type, type_of_sight, 
    ue_height, above_roof, expected):
    assert (
        extended_hata(frequency, distance, ant_height, ant_type, \
        building_height, street_width, settlement_type, type_of_sight, \
        ue_height, above_roof)
        ) == expected

#Test errors for Extended HATA
def test_extended_hata_model_value_errors():

    msg = 'Distance over 100km not compliant'

    with pytest.raises(ValueError) as ex1:
        extended_hata(4,2000000,20,'macro',20,20,'urban','los',1.5,1)

    assert msg in str(ex1)

    msg = 'Carrier frequency incorrect for Extended Hata'

    with pytest.raises(ValueError) as ex1:
        extended_hata(7,200,20,'macro',20,20,'urban','los',1.5,1)

    assert msg in str(ex1)

    #'unknown' used to test if cell neither above or below roof line
    msg = 'Could not determine if cell is above or below roof line'

    with pytest.raises(ValueError) as ex1:
        extended_hata(1,50,15,'macro',20,20,'urban','los',1.5,'unknown')

    assert msg in str(ex1)

    with pytest.raises(ValueError) as ex2:
        extended_hata(1,150,15,'macro',20,20,'urban','los',1.5,'unknown')

    assert msg in str(ex2)

    with pytest.raises(ValueError) as ex3:
        extended_hata(1,400,15,'macro',20,20,'urban','los',1.5,'unknown')

    assert msg in str(ex3)

#Prepare for testing 3GPP E-UTRA
@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, \
    building_height, street_width, settlement_type, type_of_sight, \
    ue_height, expected", [
    #stochastic component is 4 (seed=42)
    (3.5,500,10,'micro',20,20,'urban','los',1.5, (98+4)), 
    (3.5,1000,10,'micro',20,20,'urban','los',1.5, (108+4)), 
    (3.5,6000,10,'micro',20,20,'urban','los',1.5, 250),
    #stochastic component is 7 (seed=42)
    (3.5,500,10,'micro',20,20,'urban','nlos',1.5, (136+7)), 
    (3.5,500,25, 'macro',20,20,'urban','los',1.5, (98+7)), 
    (3.5,2000,25,'macro',20,20,'urban','los',1.5, (113+7)), 
    (3.5,6000,10,'macro',20,20,'urban','los',1.5, 250),
    #stochastic component is 20 (seed=42)
    (3.5,1000,25,'macro',20,20,'urban','nlos',1.5, (142+20)), 
    (3.5,6000,10,'macro',20,20,'urban','nlos',1.5, 250),
    #stochastic component is 7 (seed=42)
    (3.5,1000,35,'macro',10,20,'suburban','los',1.5, (108+7)), 
    #stochastic component is 7 + 20 (seed=42)
    (3.5,4000,35,'macro',10,20,'suburban','los',1.5, (127+7+20)),
    #stochastic component is 53 (seed=42) 
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, (121+53)), 
    (3.5,6000,10,'macro',20,20,'suburban','los',1.5, 250),
    #stochastic component is 7 (seed=42)
    (3.5,1000,35,'macro',10,20,'rural','los',1.5, (108+7)), 
    #stochastic component is 7 + 20 (seed=42)
    (3.5,4000,35,'macro',10,20,'rural','los',1.5, (127+7+20)),
    #stochastic component is 53 (seed=42) 
    (3.5,500,35,'macro',10,20,'rural','nlos',1.5, (121+53)),  
    (3.5,6000,10,'macro',20,20,'rural','nlos',1.5, 250),
    ])

def test_eval_path_loss_calc(frequency, distance, ant_height, ant_type,  
    building_height, street_width, settlement_type, type_of_sight, 
    ue_height, expected):
    assert (
        e_utra_3gpp_tr36_814(frequency, distance, ant_height, ant_type, \
        building_height, street_width, settlement_type, type_of_sight, \
        ue_height)
        ) == expected

#Prepare for testing 3GPP compatability function
@pytest.mark.parametrize("building_height, street_width, ant_height, \
    ue_height, expected", [
    (20, 20, 20, 1.5, True),
    (5, 20, 8, 1.5, False), ])

def test_check_applicability(building_height, street_width, ant_height, 
    ue_height, expected):
    assert (
        check_applicability(building_height, street_width, ant_height, 
        ue_height)
        ) == expected

def test_path_loss_calculator_errors():

    with pytest.raises(ValueError) as ex:
        path_loss_calculator(
            0.01,500,10,'micro',20,20,'urban','los',1.5,1, True
            )

    msg = 'frequency of 0.01 is NOT within correct range'

    assert msg in str(ex)

#Prepare for testing path_loss_calculator
@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, \
    building_height, street_width, settlement_type, type_of_sight, \
    ue_height, above_roof, indoor, expected", [
    (1.8,500,20,'',20,20,'urban','nlos',1.5,0, False, 429),
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, 0, False, (121+53)),
    #building penetration stochastic component is 8655567 (seed=42)
    (1.8,500,20,'',20,20,'urban','nlos',1.5,0, True, (429+8655567)),
    #building penetration stochastic component is 8655567 (seed=42)
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, 0,True,(121+53+8655567)),
])

def test_path_loss_calculator(frequency, distance, ant_height, ant_type, 
    building_height,street_width, settlement_type, type_of_sight, ue_height, 
    above_roof, indoor, expected):
    assert (
        path_loss_calculator(frequency, distance, ant_height, ant_type, 
        building_height, street_width, settlement_type, type_of_sight, 
        ue_height, above_roof, indoor)
        ) == expected

#Prepare for testing determine_path_loss
@pytest.mark.parametrize("extended_hata_path_loss, free_space_path_loss, \
    expected", [
    (100, 200, 200),
    (200, 100, 200),
    ])

def test_determine_path_loss(extended_hata_path_loss, free_space_path_loss, 
    expected):
    assert (
        determine_path_loss(extended_hata_path_loss, free_space_path_loss)
        ) == expected
