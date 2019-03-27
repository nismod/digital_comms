import pytest
from digital_comms.mobile_network.path_loss_module import (
    path_loss_calculator,
    free_space_model,
    extended_hata,
    check_applicability
)

@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, building_height, \
    street_width, settlement_type, type_of_sight, ue_height, above_roof, expected", [
    (1,20,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance <0.04 km
    # (1,50,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.04 km, above roof
    # (1,50,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.04 km, below roof
    # (1,150,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.1 km, above roof
    # (1,150,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.1 km, below roof
    # (1,400,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.2 km, above roof
    # (1,400,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.2 km, below roof
    # (1,700,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.6 km
])

def test_free_space_model(frequency, distance, ant_height, ant_type, building_height,
    street_width, settlement_type, type_of_sight, ue_height, above_roof, expected):
    assert (
        path_loss_calculator(frequency, distance, ant_height, ant_type, building_height,
        street_width, settlement_type, type_of_sight, ue_height, above_roof)
    ) == expected

def test_free_space_model_value_errors():

    #'unknown' used to test if cell neither above or below roof line
    msg = 'Could not determine if cell is above or below roof line'

    with pytest.raises(ValueError) as ex1:
        free_space_model(1,50,15,'macro',20,20,'urban','los',1.5,'unknown')

    assert msg in str(ex1)

    with pytest.raises(ValueError) as ex2:
        free_space_model(1,150,15,'macro',20,20,'urban','los',1.5,'unknown')

    assert msg in str(ex2)

    with pytest.raises(ValueError) as ex3:
        free_space_model(1,400,15,'macro',20,20,'urban','los',1.5,'unknown')

    assert msg in str(ex3)

@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, building_height, \
    street_width, settlement_type, type_of_sight, ue_height, above_roof, expected", [
    (3,20,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance <0.04 km
    # (1,50,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.04 km, above roof
    # (1,50,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.04 km, below roof
    # (1,150,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.1 km, above roof
    # (1,150,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.1 km, below roof
    # (1,400,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.2 km, above roof
    # (1,400,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.2 km, below roof
    # (1,700,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.6 km
])

def test_extended_hata_model(frequency, distance, ant_height, ant_type, building_height,
    street_width, settlement_type, type_of_sight, ue_height, above_roof, expected):
    assert (
        path_loss_calculator(frequency, distance, ant_height, ant_type, building_height,
        street_width, settlement_type, type_of_sight, ue_height, above_roof)
    ) == expected

# @pytest.mark.parametrize("frequency, distance, ant_height, ant_type, building_height, street_width, settlement_type, type_of_sight, ue_height, expected", [
#     (3.5,500,10,'micro',20,20,'urban','los',1.5, (98+4)), #stochastic component is 4 (seed=42)
#     (3.5,1000,10,'micro',20,20,'urban','los',1.5, (108+4)), #stochastic  component is 4 (seed=42)
#     (3.5,6000,10,'micro',20,20,'urban','los',1.5, 250),
#     (3.5,500,10,'micro',20,20,'urban','nlos',1.5, (136+7)), #stochastic component is 7 (seed=42)
#     (3.5,500,25, 'macro',20,20,'urban','los',1.5, (98+7)), #stochastic component is 7 (seed=42)
#     (3.5,2000,25,'macro',20,20,'urban','los',1.5, (113+7)), #stochastic component is 7 (seed=42)
#     (3.5,6000,10,'macro',20,20,'urban','los',1.5, 250),
#     (3.5,1000,25,'macro',20,20,'urban','nlos',1.5, (142+20)), #stochastic component is 20 (seed=42)
#     (3.5,6000,10,'macro',20,20,'urban','nlos',1.5, 250),
#     (3.5,1000,35,'macro',10,20,'suburban','los',1.5, (108+7)), #stochastic component is 7 (seed=42)
#     (3.5,4000,35,'macro',10,20,'suburban','los',1.5, (127+7+20)), #stochastic component is 7 + 20 (seed=42)
#     (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, (121+53)), #stochastic component is 53 (seed=42)
#     (3.5,6000,10,'macro',20,20,'suburban','los',1.5, 250),
#     (3.5,1000,35,'macro',10,20,'rural','los',1.5, (108+7)), #stochastic component is 7 (seed=42)
#     (3.5,4000,35,'macro',10,20,'rural','los',1.5, (127+7+20)), #stochastic component is 7 + 20 (seed=42)
#     (3.5,500,35,'macro',10,20,'rural','nlos',1.5, (121+53)),  #stochastic component is 53 (seed=42)
#     (3.5,6000,10,'macro',20,20,'rural','nlos',1.5, 250),
# ])

# def test_eval_path_loss_calc(frequency, distance, ant_height, ant_type, building_height, street_width, settlement_type, type_of_sight, ue_height, expected):
#     assert (path_loss_calculator(frequency, distance, ant_height, ant_type, building_height, street_width, settlement_type, type_of_sight, ue_height)) == expected

# @pytest.mark.parametrize("building_height, street_width, ant_height, ue_height, expected", [
#     (20, 20, 20, 1.5, True),
#     (5, 20, 8, 1.5, False), ])

# def test_eval_applicability(building_height, street_width, ant_height, ue_height, expected):
#     assert (check_applicability(building_height, street_width, ant_height, ue_height)) == expected

# def test_value_errors():

#     with pytest.raises(ValueError) as ex:
#         path_loss_calculator(1,500,10,'micro',20,20,'urban','los',1.5)

#     msg = 'frequency of 1 is NOT within correct range of 2-6 GHz'

#     assert msg in str(ex)

#     with pytest.raises(ValueError) as ex:
#         path_loss_calculator(3.5,500,35,'unknown',10,20,'unknown','unknown',1.5)

#     msg = 'Did not recognise parameter combination'

#     assert msg in str(ex)
