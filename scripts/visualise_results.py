#####################################
# GENERATE NETWORK LENGTH STATISTICS
######################################

def calc_total_link_length(exchanges, sp_cab_links, sp_dist_point_links, sp_premises_links, sl_cab_links, 
                            sl_dist_point_links, sl_premises_links, prems_over_lut, prems_under_lut):
    
        length_data = []
        
        for exchange in exchanges:
            for cab_link in sp_cab_links:
                if exchange['properties']['id'] == cab_link['properties']['dest']:
                    for dist_point_link in sp_dist_point_links:
                        if cab_link['properties']['origin'] == dist_point_link['properties']['dest']:
                            for premises_link in sp_premises_links:
                                if dist_point_link['properties']['origin'] == premises_link['properties']['dest']:
                                    if premises_link['properties']['origin'] in prems_over_lut:
                                        premises_distance = 'over'
                                    elif premises_link['properties']['origin'] in prems_under_lut:
                                        premises_distance = 'under'
                                    else:
                                        print('premise not in either distance lut')
                                        premises_distance = 'unknown'

                                    cab_link_length = round(cab_link['properties']['length'],2)
                                    dist_point_link_length = round(dist_point_link['properties']['length'],2)          
                                    premises_link_length = round(premises_link['properties']['length'],2)
                                    d_side_length = round(dist_point_link_length + premises_link_length,2)
                                    total_link_length = round(cab_link_length + d_side_length,2)
                                    
                                    length_data.append({
                                        'premises_id': premises_link['properties']['origin'],
                                        'exchange_id': exchange['properties']['id'],
                                        'geotype': exchange['properties']['geotype'],
                                        'cab_link_length': cab_link_length,
                                        'dist_point_link_length': dist_point_link_length,
                                        'premises_link_length': premises_link_length, 
                                        'd_side': d_side_length,
                                        'total_link_length': total_link_length,
                                        'length_type': 'shortest_path',
                                        'premises_distance': premises_distance
                                    })

        for exchange in exchanges:
            for cab_link in sl_cab_links:
                if exchange['properties']['id'] == cab_link['properties']['dest']:
                    for dist_point_link in sl_dist_point_links:
                        if cab_link['properties']['origin'] == dist_point_link['properties']['dest']:
                            for premises_link in sl_premises_links:
                                if dist_point_link['properties']['origin'] == premises_link['properties']['dest']:
                                    if premises_link['properties']['origin'] in prems_over_lut:
                                        premises_distance = 'over'
                                    elif premises_link['properties']['origin'] in prems_under_lut:
                                        premises_distance = 'under'
                                    else:
                                        print('premise not in either distance lut')
                                        premises_distance = 'unknown'

                                    cab_link_length = round(cab_link['properties']['length'],2)
                                    dist_point_link_length = round(dist_point_link['properties']['length'],2)          
                                    premises_link_length = round(premises_link['properties']['length'],2)
                                    d_side_length = round(dist_point_link_length + premises_link_length,2)
                                    total_link_length = round(cab_link_length + d_side_length,2)
                                    
                                    length_data.append({
                                        'premises_id': premises_link['properties']['origin'],
                                        'exchange_id': exchange['properties']['id'],
                                        'geotype': exchange['properties']['geotype'],
                                        'cab_link_length': cab_link_length,
                                        'dist_point_link_length': dist_point_link_length,
                                        'premises_link_length': premises_link_length, 
                                        'd_side': d_side_length,
                                        'total_link_length': total_link_length,
                                        'length_type': 'straight_line',
                                        'premises_distance': premises_distance
                                    })

        return length_data

def calc_geotype_statistics(exchanges, cabinets, dist_points, premises):

    for exchange in exchanges:
        
        cabs_over = 0
        cabs_under = 0

        if exchange['properties']['geotype'] == '>20k lines' or '>10k lines':
            distance = 2000
        elif exchange['properties']['geotype'] == '>3k lines' or '>1k lines' or '<1k lines':
            distance = 1000
        else:
            print('exchange not allocated a clustering distance of 2km or 1km')

        ex_geom = shape(exchange["geometry"])
        for cab in cabinets:
            if exchange['properties']['id'] == cab['properties']['connection']:
                cab_geom = shape(cab["geometry"])
                strt_distance = round(ex_geom.distance(cab_geom), 2)
                if strt_distance >= distance:
                    cabs_over +=1
                if strt_distance < distance:
                    cabs_under +=1

        exchange['properties']['cabs_over'] = cabs_over
        exchange['properties']['cabs_under'] = cabs_under

        dist_points_over = 0
        dist_points_under = 0

        for cab in cabinets:
            if exchange['properties']['id'] == cab['properties']['connection']:
                for dist_point in dist_points:
                    if cab['properties']['id'] == dist_point['properties']['connection']:
                        dist_point_geom = shape(dist_point["geometry"])
                        strt_distance = round(ex_geom.distance(dist_point_geom), 2)
                        if strt_distance >= distance:
                            dist_points_over +=1
                        if strt_distance < distance:
                            dist_points_under +=1

        exchange['properties']['dps_over'] = dist_points_over
        exchange['properties']['dps_under'] = dist_points_under

    return exchanges

def calculate_network_statistics(length_data, exchanges, exchange_name):

    urban_exchange_length_data = []
    under_exchange_length_data = []
    over_exchange_length_data = []

    for length in length_data:
        if (length['geotype'] == 'inner london' or length['geotype'] == 'large city' or length['geotype'] == 'small city'):

            if length['exchange_id'] == exchange_name and length['length_type'] == 'straight_line':
                urban_exchange_length_data.append(float(length['total_link_length']))

            urban_ave_length = (float(sum(urban_exchange_length_data)) / float(len(urban_exchange_length_data)))

        elif (length['geotype'] == '>20k lines' or length['geotype'] == '>10k lines' or length['geotype'] == '>3k lines' or
            length['geotype'] == '>1k lines' or length['geotype'] == '<1k lines'):

            if length['exchange_id'] == exchange_name and length['length_type'] == 'straight_line' and length['premises_distance'] == 'under': 
                under_exchange_length_data.append(float(length['total_link_length']))

            elif length['exchange_id'] == exchange_name and length['length_type'] == 'straight_line' and length['premises_distance'] == 'over': 
                over_exchange_length_data.append(float(length['total_link_length']))
                        
            if len(under_exchange_length_data) > 0:
                under_ave_length = (float(sum(under_exchange_length_data)) / float(len(under_exchange_length_data)))

            if len(over_exchange_length_data) > 0:
                over_ave_length = (float(sum(over_exchange_length_data)) / float(len(over_exchange_length_data)))

        else:
            print('no geotype found for link in length_data')
    
    return_network_stats = []

    for exchange in exchanges:
        """
        - 'am_' stands for Analysys Mason and refers to the network stats quoted
        in the 2008 report ‘The Costs of Deploying Fibre-Based next-Generation 
        Broadband Infrastructure’ produced for the Broadband Stakeholder Group 
        - 'ovr' = over
        - 'udr' = under
        
        """
        if exchange['properties']['geotype'] == 'inner london':
            am_average_lines_per_exchange = 16,812
            am_cabinets = 2,892
            am_average_lines_per_cabinet = 500
            am_distribution_points = 172,118
            am_ave_lines_per_dist_point = 8.4
            am_ave_line_length = 1240

        elif exchange['properties']['geotype'] == 'large city':
            am_average_lines_per_exchange = 15,512
            am_cabinets = 6,329
            am_average_lines_per_cabinet = 500
            am_distribution_points = 376,721
            am_ave_lines_per_dist_point = 8.4
            am_ave_line_length = 1780

        elif exchange['properties']['geotype'] == 'small city':
            am_average_lines_per_exchange = 15,527
            am_cabinets = 5,590
            am_average_lines_per_cabinet = 500
            am_distribution_points = 332,713
            am_ave_lines_per_dist_point = 8.4
            am_ave_line_length = 1800

        elif exchange['properties']['geotype'] == '>20k lines':
            am_udr_average_lines_per_exchange = 17089
            am_udr_cabinets = 6008
            am_udr_average_lines_per_cabinet = 475
            am_udr_distribution_points = 365,886
            am_udr_average_lines_per_dist_point = 7.8
            am_udr_average_line_length = 1500

            am_ovr_average_lines_per_exchange = 10449
            am_ovr_cabinets = 4362
            am_ovr_average_lines_per_cabinet = 400
            am_ovr_distribution_points = 223708
            am_ovr_average_lines_per_dist_point = 7.8
            am_ovr_average_line_length = 4830

        elif geotype == '>10k lines':
            
            am_udr_average_lines_per_exchange = 10728
            am_udr_cabinets = 9679
            am_udr_average_lines_per_cabinet = 450
            am_udr_distribution_points = 604925
            am_udr_average_lines_per_dist_point =7.2
            am_udr_average_line_length = 1400

            am_ovr_average_lines_per_exchange = 3826
            am_ovr_cabinets = 4142
            am_ovr_average_lines_per_cabinet = 375
            am_ovr_distribution_points = 215740
            am_ovr_average_lines_per_dist_point = 7.2
            am_ovr_average_line_length = 4000

        elif geotype == '>3k lines':

            am_udr_average_lines_per_exchange = 2751
            am_udr_cabinets = 13455
            am_udr_average_lines_per_cabinet = 205
            am_udr_distribution_points = 493569
            am_udr_average_lines_per_dist_point = 5.6
            am_udr_average_line_length = 730

            am_ovr_average_lines_per_exchange = 3181
            am_ovr_cabinets = 22227
            am_ovr_average_lines_per_cabinet = 144
            am_ovr_distribution_points = 570745
            am_ovr_average_lines_per_dist_point = 5.6
            am_ovr_average_line_length = 4830

        elif geotype == '>1k lines':

            am_udr_average_lines_per_exchange = 897
            am_udr_cabinets = 5974
            am_udr_average_lines_per_cabinet = 185
            am_udr_distribution_points = 246555
            am_udr_average_lines_per_dist_point = 4.5
            am_udr_average_line_length = 620

            am_ovr_average_lines_per_exchange = 935
            am_ovr_cabinets = 9343
            am_ovr_average_lines_per_cabinet = 123
            am_ovr_distribution_points = 257043
            am_ovr_average_lines_per_dist_point = 4.5
            am_ovr_average_line_length = 4090

        elif geotype == '<1k lines':

            am_udr_average_lines_per_exchange = 190
            am_udr_cabinets = 0
            am_udr_average_lines_per_cabinet = 0
            am_udr_distribution_points = 130706
            am_udr_average_lines_per_dist_point = 3.4
            am_udr_average_line_length = 520
            
            am_ovr_average_lines_per_exchange = 305
            am_ovr_cabinets = 0
            am_ovr_average_lines_per_cabinet = 0
            am_ovr_distribution_points = 209571
            am_ovr_average_lines_per_dist_point = 3.4
            am_ovr_average_line_length = 4260

        else:
            print('no geotype found for AM reference statistics')

        if (exchange['properties']['geotype'] == 'inner london' or 
                exchange['properties']['geotype'] == 'large city' or 
                exchange['properties']['geotype'] == 'small city'):
        
            return_network_stats.append({
                'exchange_id': exchange['properties']['id'],
                'geotype': exchange['properties']['geotype'],
                'distance_type':'urban',
                'am_ave_lines_per_ex': am_average_lines_per_exchange,
                'total_lines': exchange['properties']['prems_under'] + exchange['properties']['prems_over'], 
                'am_cabinets': am_cabinets,
                'total_cabinets': exchange['properties']['cabs_under'] + exchange['properties']['cabs_over'],
                'am_ave_lines_per_cab': am_average_lines_per_cabinet, 
                'ave_lines_per_cab': 'TODO',
                'am_distribution_points': am_distribution_points,
                'total_dps': exchange['properties']['dps_under'] + exchange['properties']['dps_over'],
                'am_ave_lines_per_dist_point': am_ave_lines_per_dist_point,
                'ave_lines_per_dist_point': 'TODO',
                'am_ave_line_length': am_ave_line_length,
                'ave_line_length': round(urban_ave_length, 2),
            })
            
        elif (length['geotype'] == '>20k lines' or length['geotype'] == '>10k lines' or 
                length['geotype'] == '>3k lines' or length['geotype'] == '>1k lines' or 
                length['geotype'] == '<1k lines'):

            return_network_stats.append({
                'exchange_id': exchange['properties']['id'],
                'geotype': exchange['properties']['geotype'],
                'distance_type':'under_threshold',
                'am_ave_lines_per_ex': am_udr_average_lines_per_exchange,
                'total_lines': exchange['properties']['prems_under'] + exchange['properties']['prems_over'], 
                'am_cabinets': am_udr_cabinets,
                'total_cabinets': exchange['properties']['cabs_under'] + exchange['properties']['cabs_over'],
                'am_ave_lines_per_cab': am_udr_average_lines_per_cabinet, 
                'ave_lines_per_cab': 'TODO',
                'am_distribution_points': am_udr_distribution_points,
                'total_dps': exchange['properties']['dps_under'] + exchange['properties']['dps_over'],
                'am_ave_lines_per_dist_point': am_udr_average_lines_per_dist_point,
                'ave_lines_per_dist_point': 'TODO',
                'am_ave_line_length': am_udr_average_line_length,
                'ave_line_length': round(under_ave_length,2),
            })
            
            return_network_stats.append({
                'exchange_id': exchange['properties']['id'],
                'geotype': exchange['properties']['geotype'],
                'distance_type':'over_threshold',
                'am_ave_lines_per_ex': am_ovr_average_lines_per_exchange,
                'total_lines': exchange['properties']['prems_under'] + exchange['properties']['prems_over'], 
                'am_cabinets': am_ovr_cabinets,
                'total_cabinets': exchange['properties']['cabs_under'] + exchange['properties']['cabs_over'],
                'am_ave_lines_per_cab': am_ovr_average_lines_per_cabinet, 
                'ave_lines_per_cab': 'TODO',
                'am_distribution_points': am_ovr_distribution_points,
                'total_dps': exchange['properties']['dps_under'] + exchange['properties']['dps_over'],
                'am_ave_lines_per_dist_point': am_ovr_average_lines_per_dist_point,
                'ave_lines_per_dist_point': 'TODO',
                'am_ave_line_length': am_ovr_average_line_length,
                'ave_line_length': round(over_ave_length,2),
            })

    return return_network_stats

#####################################
# VISUALISE NETWORK STATS
#####################################

def plot_length_data(data, exchange_name):

    e_side_sp_length = []
    d_side_sp_length = []
    dist_point_sp_length = []
    total_link_sp_length = []
    
    e_side_sl_length = []
    d_side_sl_length = []
    dist_point_sl_length = []
    total_link_sl_length = []

    for datum in data:
        if datum['length_type'] == 'shortest_path':
            e_side_sp_length.append(datum['cab_link_length'])
            d_side_sp_length.append(datum['d_side'])
            dist_point_sp_length.append(datum['premises_link_length'])
            total_link_sp_length.append(datum['total_link_length'])
        elif datum['length_type'] == 'straight_line':
            e_side_sl_length.append(datum['cab_link_length'])
            d_side_sl_length.append(datum['d_side'])
            dist_point_sl_length.append(datum['premises_link_length'])
            total_link_sl_length.append(datum['total_link_length'])

    #specify bins
    e_side_bins = np.linspace(0, 4500, 100)
    d_side_bins = np.linspace(0, 3500, 100)
    final_drop_bins = np.linspace(0, 100, 10)
    total_bins = np.linspace(0, 7000, 100)

    #setup and plot
    f, axarr = plt.subplots(2, 2)
    axarr[0, 0].hist(e_side_sp_length, e_side_bins, alpha=0.5, label='Shortest Path')
    axarr[0, 0].hist(e_side_sl_length, e_side_bins, alpha=0.5, label='Straight Line')
    axarr[0, 0].set_title('E-Side Loop Length')
    axarr[0, 1].hist(d_side_sp_length, d_side_bins, alpha=0.5, label='Shortest Path')
    axarr[0, 1].hist(d_side_sl_length, d_side_bins, alpha=0.5, label='Straight Line')
    axarr[0, 1].set_title('D-Side Loop Length')
    axarr[1, 0].hist(dist_point_sp_length, final_drop_bins, alpha=0.5, label='Shortest Path')
    axarr[1, 0].hist(dist_point_sl_length, final_drop_bins, alpha=0.5, label='Straight Line')
    axarr[1, 0].set_title('Final Drop Length')
    axarr[1, 1].hist(total_link_sp_length, total_bins, alpha=0.5, label='Shortest Path')
    axarr[1, 1].hist(total_link_sl_length, total_bins, alpha=0.5, label='Straight Line')
    axarr[1, 1].set_title('Total Loop Length')

    plt.legend(loc='upper right')
    f.subplots_adjust(hspace=0.5)

    directory = os.path.join(DATA_INTERMEDIATE, exchange_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(DATA_INTERMEDIATE, exchange_name, 'network_stats.png'), bbox_inches='tight')



 # # # # Generate loop lengths
    # # # print('calculating loop length stats')
    # # # length_data = calc_total_link_length(geojson_layer2_exchanges, 
    # # #                                         geojson_layer3_cabinets_sp_links, geojson_layer4_distributions_sp_links, geojson_layer5_premises_sp_links,
    # # #                                         geojson_layer3_cabinets_sl_links, geojson_layer4_distributions_sl_links, geojson_layer5_premises_sl_links,
    # # #                                         prems_over_lut, prems_under_lut)

    # # # # Calculate geotype statistics
    # # # print('calculating geotype statistics')
    # # # exchanges = calc_geotype_statistics(geojson_layer2_exchanges, geojson_layer3_cabinets, geojson_layer4_distributions, geojson_layer5_premises)

    # # # # Calculate network statistics
    # # # print('calculating network statistics')
    # # # network_stats = calculate_network_statistics(length_data, exchanges, exchange_name)

    # # # # Plot network statistics
    # # # print('plotting network statistics')
    # # # plot_length_data(length_data, exchange_name)
