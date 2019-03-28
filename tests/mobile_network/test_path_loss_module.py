import pytest
from digital_comms.mobile_network.path_loss_module import (
    path_loss_calculator,
    free_space,
    extended_hata,
    check_applicability
)

@pytest.mark.parametrize("frequency, distance, ant_height, ue_height, expected", [
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

@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, building_height, \
    street_width, settlement_type, type_of_sight, ue_height, above_roof, expected", [
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
    #change distances
    #test 90m
    # # test distance 0.09 km, above roof, stochastic component =   
    # (1.8,90,20,'',20,20,'urban','los',1.5,1, 0 ), 
    # # test distance 0.09 km, below roof, stochastic component =   
    # (1.8,90,20,'',20,20,'urban','nlos',1.5,0, 4873), 
    #test 500m    
    # test distance 0.05 km, above roof, stochastic component =   
    (1.8,500,20,'',20,20,'urban','los',1.5,1, 0 ), 
    # # test distance 0.05 km, below roof, stochastic component =   
    # (1.8,90,20,'',20,20,'urban','nlos',1.5,0, 4873), 
    
    
    
    # ####suburban####
    # # test distance >0.04 km, above roof, stochastic component = 338 
    # (0.8,200,20,'',20,20,'suburban','los',1.5,1, 529),  
    # # test distance >0.04 km, below roof, stochastic component = 4648 
    # (0.8,200,20,'',20,20,'suburban','nlos',1.5,0, 4789), 
    # # test distance 0.5 km, above roof, stochastic component = 112  
    # (0.8,500,20,'',20,20,'suburban','los',1.5,1, 274), 
    # # test distance 0.5 km, above roof, stochastic component = 184  
    # (0.8,500,20,'',20,20,'suburban','los',1.5,0, 346), 
    # ####rural####
    # # test distance >0.04 km, above roof, stochastic component = 338 
    # (1.8,200,20,'',20,20,'rural','los',1.5,1, 441), 




    # (1,150,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.1 km, above roof
    # (1,150,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.1 km, below roof
    # (1,400,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.2 km, above roof
    # (1,400,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.2 km, below roof
    # (1,700,15,'macro',20,20,'urban','los',1.5,1, 6), # test distance >0.6 km
])

def test_extended_hata(frequency, distance, ant_height, ant_type, building_height,
    street_width, settlement_type, type_of_sight, ue_height, above_roof, expected):
    assert (
        extended_hata(frequency, distance, ant_height, ant_type, building_height,
        street_width, settlement_type, type_of_sight, ue_height, above_roof)
    ) == expected

#error for providing >3ghz
def test_extended_hata_model_value_errors():

    msg = 'Distance over 100km not compliant'

    with pytest.raises(ValueError) as ex1:
        extended_hata(4,2000000,20,'macro',20,20,'urban','los',1.5,1)

    assert msg in str(ex1)

    msg = 'Carrier frequency incorrect for Extended HATA'

    with pytest.raises(ValueError) as ex1:
        extended_hata(4,200,20,'macro',20,20,'urban','los',1.5,1)

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
