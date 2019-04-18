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
    #seed=42
    #expected value is: (deterministic path loss, stochastic component)
    (0.8,1000,20,1.5,(90.46+0.75)),
    (0.8,2000,20,1.5,(96.48+0.75)),
    (0.8,3000,20,1.5,(100+0.75)),
    (0.8,4000,20,1.5,(102.5+0.75)),
    (0.8,5000,20,1.5,(104.44+0.75)),
    (1.8,1000,20,1.5,(97.51+0.75)),
    (1.8,2000,20,1.5,(103.53+0.75)),
    (1.8,3000,20,1.5,(107.05+0.75)),
    (1.8,4000,20,1.5,(109.55+0.75)),
    (1.8,5000,20,1.5,(111.48+0.75)),
    (2.6,1000,20,1.5,(100.7+0.75)),
    (2.6,2000,20,1.5,(106.72+0.75)),
    (2.6,3000,20,1.5,(110.24+0.75)),
    (2.6,4000,20,1.5,(112.74+0.75)),
    (2.6,5000,20,1.5,(114.68+0.75)),
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
    # test distance <0.04 km
    (0.8,20,20,'macro',20,20,'urban','los',1.5,1,(94.03+0.61)),
    # test distance <0.04 km, above roof
    (0.1,200,20,'macro',20,20,'urban','los',1.5,1,(117.3+0.25)),
    # test distance >0.04 km, below roof
    (0.1,200,20,'',20,20,'urban','nlos',1.5,0,(117.3+0.19)),
    # test distance >0.04 km, above roof
    (0.8,200,20,'',20,20,'urban','los',1.5,1, (169.08+0.25)),
    # test distance >0.04 km, below roof
    (0.8,200,20,'',20,20,'urban','nlos',1.5,0, (169.08+0.19)),
    # test distance >0.04 km, above roof
    (1.8,200,20,'',20,20,'urban','los',1.5,1, (224.67+0.25)),
    # test distance >0.04 km, below roof
    (1.8,200,20,'',20,20,'urban','nlos',1.5,0, (round(224.86,2))),
    # test distance >0.04 km, above roof
    (2.1,200,20,'',20,20,'urban','los',1.5,1, (228.72+0.25)),
    # test distance >0.04 km, below roof
    (2.1,200,20,'',20,20,'urban','nlos',1.5,0, (228.72+0.19)),
    ####suburban####
    # test distance >0.04 km, above roof
    (0.8,200,20,'',20,20,'suburban','los',1.5,1, (141.2+0.25)),
    # test distance >0.04 km, below roof
    (0.8,200,20,'',20,20,'suburban','nlos',1.5,0, (141.2+0.19)),
    # test distance 0.5 km, above roof
    (0.8,500,20,'',20,20,'suburban','los',1.5,1, (round(162.23,2))),
    # test distance 0.5 km, above roof
    (0.8,500,20,'',20,20,'suburban','los',1.5,0, (round(162.21,2))),
    ####rural####
    # test distance >0.04 km, above roof
    (1.8,200,20,'',20,20,'rural','los',1.5,1, (52.57+0.25)),
    #####test 500m####
    # test distance 0.05 km, above roof
    (1.8,500,20,'',20,20,'urban','los',1.5,1, (round(245.4+0.3,2))),
    # test distance 0.05 km, below roof
    (1.8,500,20,'',20,20,'urban','nlos',1.5,0, (245.4+0.28)),
    #change distances
    #test 90m (0.04< d <0.1)
    # test distance 0.09 km, above roof
    (1.8,90,20,'',20,20,'urban','los',1.5,1, (round(134.67+0.35,2))),
    # test distance 0.09 km, below roof
    (1.8,90,20,'',20,20,'urban','nlos',1.5,0, (round(134.67+0.28,2))),
    #test 5km
    # test distance 5 km, above roof
    (1.8,5000,20,'',20,20,'urban','los',1.5,1, (297.49+0.25)),
    # test distance 5 km, above roof
    (1.8,5000,20,'',20,20,'rural','los',1.5,1, (125.39+0.25)),
    #test 20km
    # test distance 20 km, above roof
    (0.7,20000,20,'',20,20,'urban','los',1.5,1, (269.77+0.25)),
    (0.7,20000,20,'',20,20,'rural','los',1.5,1, (143.77+0.25)),
    #test 21km
    # test distance 21 km, above roof
    (0.7,21000,20,'',20,20,'urban','los',1.5,1, (272.91+0.25)),
    (0.7,21000,20,'',20,20,'rural','los',1.5,1, (146.91+0.25)),
    # test distance 25 km, above roof
    (0.7,25000,20,'',20,20,'urban','los',1.5,1, (282.72+0.25)),
    (0.7,25000,20,'',20,20,'rural','los',1.5,1, (156.72+0.25)),
    #test 50km
    # test distance 50 km, above roof
    (0.7,50000,20,'',20,20,'urban','los',1.5,1, (330.35+0.25)),
    (0.7,50000,20,'',20,20,'rural','los',1.5,1, (204.35+0.25)),
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
    #stochastic component is 0.68 (seed=42)
    (3.5,500,10,'micro',20,20,'urban','los',1.5, (round(98.26+0.67,2))),
    (3.5,1000,10,'micro',20,20,'urban','los',1.5, (round(107.72+0.67,2))),
    (3.5,6000,10,'micro',20,20,'urban','los',1.5, 250),
    # #stochastic component is 0.56 (seed=42)
    (3.5,500,10,'micro',20,20,'urban','nlos',1.5, (135.90+0.56)),
    (3.5,500,25, 'macro',20,20,'urban','los',1.5, (round(98.26+0.56,2))),
    (3.5,2000,25,'macro',20,20,'urban','los',1.5, (112.6+0.56)),
    (3.5,6000,10,'macro',20,20,'urban','los',1.5, 250),
    #stochastic component is 0.42 (seed=42)
    (3.5,1000,25,'macro',20,20,'urban','nlos',1.5, (round(141.69+0.42,2))),
    (3.5,6000,10,'macro',20,20,'urban','nlos',1.5, 250),
    #stochastic component is 0.56 (seed=42)
    (3.5,1000,35,'macro',10,20,'suburban','los',1.5, (107.74+0.56)),
    #stochastic component is 0.56 & 0.42 (seed=42)
    (3.5,4000,35,'macro',10,20,'suburban','los',1.5, (round(126.73+0.56+0.42,2))),
    #stochastic component is 0.34 (seed=42)
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, (121.39+0.34)),
    (3.5,6000,10,'macro',20,20,'suburban','los',1.5, 250),
    #stochastic component is 0.56 (seed=42)
    (3.5,1000,35,'macro',10,20,'rural','los',1.5, (107.74+0.56)),
    #stochastic component is 0.56 + 0.42 (seed=42)
    (3.5,4000,35,'macro',10,20,'rural','los',1.5, (round(126.73+0.56+0.42,2))),
    #stochastic component is 0.34 (seed=42)
    (3.5,500,35,'macro',10,20,'rural','nlos',1.5, (121.39+0.34)),
    (3.5,6000,10,'macro',20,20,'rural','nlos',1.5, 250),
    ])

def test_eval_path_loss_calc(frequency, distance, ant_height, ant_type,
    building_height, street_width, settlement_type, type_of_sight,
    ue_height, expected):
    print(e_utra_3gpp_tr36_814(frequency, distance, ant_height, ant_type, \
        building_height, street_width, settlement_type, type_of_sight, \
        ue_height))
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
    (1.8,500,20,'',20,20,'urban','nlos',1.5,0, False, (245.4+0.28)),
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, 0, False, (121.39+0.34)),
    (1.8,500,20,'',20,20,'urban','nlos',1.5,0, True, (245.4+0.28+13.49)),
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, 0,True,(121.39+0.34+13.49)),
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
