#####################################
# INTEGRATE WTP AND WTA HOUSEHOLD DATA INTO PREMIses
#####################################

def read_msoa_data(lad_ids):
    """
    MSOA data contains individual level demographic characteristics including:
        - PID - Person ID
        - MSOA - Area ID
        - DC1117EW_C_SEX - Gender
        - DC1117EW_C_AGE - Age
        - DC2101EW_C_ETHPUK11 - Ethnicity
        - HID - Household ID
        - year - year
    """

    MSOA_data = []

    msoa_lad_id_files = {
        lad: os.path.join(DATA_RAW_INPUTS,'demographic_scenario_data','msoa_2018','ass_{}_MSOA11_2018.csv'.format(lad))
        for lad in lad_ids
    }

    pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'demographic_scenario_data','msoa_2018') + '/*.csv', recursive=True)

    for filename in msoa_lad_id_files.values():
        with open(os.path.join(filename), 'r') as system_file:
            year_reader = csv.reader(system_file)
            next(year_reader, None)
            # Put the values in the population dict
            for line in year_reader:
                MSOA_data.append({
                    'PID': line[0],
                    'MSOA': line[1],
                    'lad': filename[-25:-16],
                    'gender': line[2],
                    'age': line[3],
                    'ethnicity': line[4],
                    'HID': line[5],
                    'year': int(filename[-8:-4]),
                })

    return MSOA_data

def read_age_data():
    """
    Contains data on fixed broadband adoption by age :
        - Age
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'age.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'age': row[0],
                'age_wta': int(row[1])
            })

        return my_data

def read_gender_data():
    """
    Contains data on fixed broadband adoption by socio-economic status (ses):
        - ses
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'gender.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'gender': row[0],
                'gender_wta': int(row[1])
            })

        return my_data

def read_nation_data():
    """
    Contains data on fixed broadband adoption by nation:
        - nation
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'nation.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'nation': row[0],
                'nation_wta': int(row[1])
            })

        return my_data

def read_urban_rural_data():
    """
    Contains data on fixed broadband adoption by urban_rural:
        - urban_rural
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'urban_rural.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'urban_rural': row[0],
                'urban_rural_wta': int(row[1])
            })

        return my_data

def add_country_indicator(data):

    for person in data:

        if person['lad'].startswith("E"):
            person['nation'] = 'england'
        if person['lad'].startswith("S"):
            person['nation'] = 'scotland'
        if person['lad'].startswith("w"):
            person['nation'] = 'wales'
        if person['lad'].startswith("N"):
            person['nation'] = 'northern ireland'

    return data

def read_ses_data():
    """
    Contains data on fixed broadband adoption by socio-economic status (ses):
        - ses
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'ses.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'ses': row[0],
                'ses_wta': int(row[1])
            })

        return my_data

def add_data_to_MSOA_data(consumer_data, population_data, variable):
    """
    Take the WTP lookup table for all ages. Add to the population data based on age.
    """
    d1 = {d[variable]:d for d in consumer_data}

    population_data = [dict(d, **d1.get(d[variable], {})) for d in population_data]

    return population_data

def read_oa_data():
    """
    MSOA data contains individual level demographic characteristics including:
        - HID - Household ID
        - OA - Output Area ID
        - ses - Household Socio-Economic Status
        - year - year
    """

    OA_data = []

    oa_lad_id_files = {
        lad: os.path.join(DATA_RAW_INPUTS, 'demographic_scenario_data','oa_2018','ass_hh_{}_OA11_2018.csv'.format(lad))
        for lad in lad_ids
    }

    for filename in oa_lad_id_files.values():
        # Open file
        with open(filename, 'r') as year_file:
            year_reader = csv.reader(year_file)
            next(year_reader, None)
            # Put the values in the population dict
            for line in year_reader:
                OA_data.append({
                    'HID': line[0],
                    'OA': line[1],
                    'lad': filename[-23:-14],
                    'ses': line[12],
                    'year': int(filename[-8:-4]),
                })

    return OA_data

def convert_ses_grades(data):

    for household in data:
        if household['ses'] == '1':
            household['ses'] = 'AB'
        elif household['ses'] == '2':
            household['ses'] = 'AB'
        elif household['ses'] == '3':
            household['ses'] = 'C1'
        elif household['ses'] == '4':
            household['ses'] = 'C1'
        elif household['ses'] == '5':
            household['ses'] = 'C2'
        elif household['ses'] == '6':
            household['ses'] = 'DE'
        elif household['ses'] == '7':
            household['ses'] = 'DE'
        elif household['ses'] == '8':
            household['ses'] = 'DE'
        elif household['ses'] == '9':
            household['ses'] = 'students'

    return data

def merge_two_lists_of_dicts(msoa_list_of_dicts, oa_list_of_dicts, parameter1, parameter2, parameter3):
    """
    Combine the msoa and oa dicts using the household indicator and year keys.
    """
    d1 = {(d[parameter1], d[parameter2], d[parameter3]):d for d in oa_list_of_dicts}

    msoa_list_of_dicts = [dict(d, **d1.get((d[parameter1], d[parameter2], d[parameter3]), {})) for d in msoa_list_of_dicts]

    return msoa_list_of_dicts

def get_missing_ses_key(data):

    complete_data = []
    missing_ses = []

    for prem in data:
        if 'ses' in prem and 'ses_wta' in prem:
            complete_data.append({
                'PID': prem['PID'],
                'MSOA': prem['MSOA'],
                'lad': prem['lad'],
                'gender': prem['gender'],
                'age': prem['age'],
                'ethnicity': prem['ethnicity'],
                'HID': prem['HID'],
                'year': prem['year'],
                'nation': prem['nation'],
                'age_wta': prem['age_wta'],
                'gender_wta': prem['gender_wta'],
                'OA': prem['OA'],
                'ses': prem['ses'],
                'ses_wta': prem['ses_wta'],
            })
        else:
            missing_ses.append({
                'PID': prem['PID'],
                'MSOA': prem['MSOA'],
                'lad': prem['lad'],
                'gender': prem['gender'],
                'age': prem['age'],
                'ethnicity': prem['ethnicity'],
                'HID': prem['HID'],
                'year': prem['year'],
                'nation': prem['nation']
            })

    return complete_data, missing_ses

def calculate_adoption_propensity(data):

    for person in data:
        person['wta'] = person['age_wta'] * person['gender_wta'] * person['ses_wta']

    return data

def calculate_wtp(data):

    for person in data:
        person['wta'] = person['age_wta'] * person['gender_wta'] * person['ses_wta']

        if person['wta'] < 1800000:
            person['wtp'] = 20
        elif person['wta'] > 1800000 and  person['wta'] < 2200000:
            person['wtp'] = 30
        elif person['wta'] > 2200000 and  person['wta'] < 2600000:
            person['wtp'] = 40
        elif person['wta'] > 2600000 and  person['wta'] < 3000000:
            person['wtp'] = 50
        elif person['wta'] > 3000000:
            person['wtp'] = 60
    return data


def aggregate_wtp_and_wta_by_household(data):
    """
    Aggregate wtp by household by Household ID (HID), Local Authority District (lad) and year.
    """
    d = defaultdict(lambda: defaultdict(int))

    group_keys = ['HID','lad', 'year']
    sum_keys = ['wta','wtp']

    for item in data:
        for key in sum_keys:
            d[itemgetter(*group_keys)(item)][key] += item[key]

    results = [{**dict(zip(group_keys, k)), **v} for k, v in d.items()]

    return results

def read_premises_data(exchange_area):
    """
    Reads in premises points from the OS AddressBase data (.csv).

    Data Schema
    ----------
    * id: :obj:`int`
        Unique Premises ID
    * oa: :obj:`str`
        ONS output area code
    * residential address count: obj:'str'
        Number of residential addresses
    * non-res address count: obj:'str'
        Number of non-residential addresses
    * postgis geom: obj:'str'
        Postgis reference
    * E: obj:'float'
        Easting coordinate
    * N: obj:'float'
        Northing coordinate

    """
    premises_data = []

    #pathlist = glob.iglob(os.path.join(DATA_BUILDING_DATA, 'layer_5_premises') + '/*.csv', recursive=True)

    pathlist = []
    pathlist.append(os.path.join(DATA_BUILDING_DATA, 'layer_5_premises', 'blds_with_functions_en_E12000006.csv'))

    exchange_geom = shape(exchange_area['geometry'])
    exchange_bounds = shape(exchange_area['geometry']).bounds

    for path in pathlist:
        with open(os.path.join(path), 'r') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            for line in reader:
                if (exchange_bounds[0] <= float(line[8]) and exchange_bounds[1] <= float(line[7]) and 
                    exchange_bounds[2] >= float(line[8]) and exchange_bounds[3] >= float(line[7])):
                    premises_data.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [float(line[8]), float(line[7])]
                        },
                        'properties': {
                            'id': 'premise_' + line[0],
                            'oa': line[1],
                            'residential_address_count': line[3],
                            'non_residential_address_count': line[4],
                            #'function': line[5],
                            #'postgis_geom': line[6],
                            # 'HID': prem['HID'],
                            # 'lad': prem['lad'],
                            # 'year': prem['year'],
                            # 'wta': prem['wta'],
                            # 'wtp': prem['wtp'],
                        }
                    })

    # remove 'None' and replace with '0'
    for idx, row in enumerate(premises_data):
        if row['properties']['residential_address_count'] == 'None':
            premises_data[idx]['properties']['residential_address_count'] = '0'
        if row['properties']['non_residential_address_count'] == 'None':
            premises_data[idx]['properties']['non_residential_address_count'] = '0'

    for row in premises_data:
        row['properties']['residential_address_count'] = int(row['properties']['residential_address_count'])
        row['properties']['non_residential_address_count'] = int(row['properties']['non_residential_address_count'])

    output = [premise for premise in premises_data if exchange_geom.contains(shape(premise['geometry']))]

    return output

def expand_premises(pemises_data):
    """
    Take a single address with multiple units, and expand to get a dict for each unit.
    """
    processed_pemises_data = []

    [processed_pemises_data.extend([entry]*entry['residential_address_count']) for entry in pemises_data]

    return processed_pemises_data

def merge_prems_and_housholds(premises_data, household_data):
    """
    Merges two aligned datasets, zipping row to row.
    Deals with premises_data having multiple repeated dict references due to expand function.
    """
    result = [a.copy() for a in premises_data]

    [a.update(b) for a, b in zip(result, household_data)]

    return result

###########################################################################################################

 # ####
    # # Integrate WTP and WTA household data into premises
    # print('Loading MSOA data')
    # MSOA_data = read_msoa_data(lad_ids)

    # print('Loading age data')
    # age_data = read_age_data()

    # print('Loading gender data')
    # gender_data = read_gender_data()

    # print('Loading nation data')
    # nation_data = read_nation_data()

    # print('Loading urban_rural data')
    # urban_rural_data = read_urban_rural_data()

    # print('Add country indicator')
    # MSOA_data = add_country_indicator(MSOA_data)

    # print('Adding adoption data to MSOA data')
    # MSOA_data = add_data_to_MSOA_data(age_data, MSOA_data, 'age')
    # MSOA_data = add_data_to_MSOA_data(gender_data, MSOA_data, 'gender')

    # print('Loading OA data')
    # oa_data = read_oa_data()

    # print('Match and convert social grades from NS-Sec to NRS')
    # oa_data = convert_ses_grades(oa_data)

    # print('Loading ses data')
    # ses_data = read_ses_data()

    # print('Adding ses adoption data to OA data')
    # oa_data = add_data_to_MSOA_data(ses_data, oa_data, 'ses')

    # print('Adding MSOA data to OA data')
    # final_data = merge_two_lists_of_dicts(MSOA_data, oa_data, 'HID', 'lad', 'year')

    # print('Catching any missing data')
    # final_data, missing_data = get_missing_ses_key(final_data)

    # print('Calculate product of adoption factors')
    # final_data = calculate_adoption_propensity(final_data)

    # print('Calculate willingness to pay')
    # final_data = calculate_wtp(final_data)

    # print('Aggregating WTP by household')
    # household_wtp = aggregate_wtp_and_wta_by_household(final_data)

    # print('Expand premises entries')
    # premises = expand_premises(premises)

    # print('Adding household data to premises')
    # premises = merge_prems_and_housholds(premises, household_wtp)
    ###