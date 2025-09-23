from math import sqrt

'''
Provides functions to aggregate different types of indicator values.
See Section 8 of the ACS General Handbook for more information on the calculations.
https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_general_handbook_2020.pdf
'''

def aggregate_count_values(count_values):
    '''
    Aggregates count values.
    '''
    if any(value is None for value in count_values):
        return None
    
    return sum(count_values)

def aggregate_count_moe_values(moe_values):
    '''
    Aggregates count margin of error values.
    '''
    if any(moe is None for moe in moe_values):
        return None
    
    return round(sqrt(sum(moe ** 2 for moe in moe_values)), 2)

def aggregate_percentage_values(count_values, universe_values):
    '''
    Aggregates percentage values.
    '''
    if any(value is None for value in count_values) or any(value is None for value in universe_values):
        return None
    elif sum(universe_values) == 0:
        return None
    
    return round(sum(count_values) / sum(universe_values) * 100, 2)

def aggregate_percentage_moe_values(count_values, universe_values, count_moe_values, universe_moe_values):
    '''
    Aggregates percentage margin of error values.
    '''
    if any(value is None for value in count_values) or any(value is None for value in universe_values):
        return None
    elif sum(universe_values) == 0:
        return None
    
    count_moe_sum_squares = sum(moe ** 2 for moe in count_moe_values)
    universe_moe_sum_squares = sum(moe ** 2 for moe in universe_moe_values)
    aggregate_percentage_value = aggregate_percentage_values(count_values, universe_values)
    
    return round(sqrt((count_moe_sum_squares - (aggregate_percentage_value / 100) ** 2 * universe_moe_sum_squares)) / sum(universe_values) * 100, 2)

def aggregate_median_values(median_values, universe_values):
    '''
    Aggregates median values.
    '''
    return __aggregate_weighted_averages(median_values, universe_values)

def aggregate_median_moe_values(median_values, universe_values, median_moe_values, universe_moe_values):
    '''
    Aggregates median margin of error values.
    '''
    return __aggregate_weighted_average_moes(median_values, universe_values, median_moe_values, universe_moe_values)

def aggregate_average_values(average_values, universe_values,):
    '''
    Aggregates average values.
    '''
    return __aggregate_weighted_averages(average_values, universe_values)

def aggregate_average_moe_values(average_values, universe_values, average_moe_values, universe_moe_values):
    '''
    Aggregates average margin of error values.
    '''
    return __aggregate_weighted_average_moes(average_values, universe_values, average_moe_values, universe_moe_values)

def aggregate_rate_values(count_values, universe_values, rate_per):
    '''
    Aggregates rate values.
    '''
    if any(value is None for value in count_values) or any(value is None for value in universe_values):
        return None
    elif sum(universe_values) == 0:
        return None
    
    return round(sum(count_values) / sum(universe_values) * rate_per, 2)

def aggregate_rate_moe_values(count_values, universe_values, count_moe_values, universe_moe_values, rate_per):
    '''
    Aggregates rate margin of error values.
    '''
    if any(value is None for value in count_values) or any(value is None for value in universe_values):
        return None
    elif sum(universe_values) == 0:
        return None

    count_moe = aggregate_count_moe_values(count_moe_values)
    universe_moe = aggregate_count_moe_values(universe_moe_values)
    
    return round(
        sqrt(count_moe ** 2 + (aggregate_rate_values(count_values, universe_values, rate_per) ** 2 * universe_moe ** 2))
        /
        sum(universe_values), 2
    )

def aggregate_index_values(index_values):
    return NotImplementedError

def aggregate_index_moe_values(index_values, index_moe_values):
    return NotImplementedError

def __aggregate_weighted_averages(values, weights):
    '''
    Aggregates weighted average values.
    '''
    if any(value is None for value in values) or any(value is None for value in weights):
        return None
    elif sum(weights) == 0:
        return None
    
    weighted_sum = sum(value * weight for value, weight in zip(values, weights))
    total_weight = sum(weights)
    
    return round(weighted_sum / total_weight, 2)

def __aggregate_weighted_average_moes(values, weights, value_moes, weight_moes):
    '''
    Aggregates weighted average margin of error values.
    '''
    if any(value is None for value in values) or any(value is None for value in weights):
        return None
    elif any(moe is None for moe in value_moes) or any(moe is None for moe in weight_moes):
        return None
    elif sum(weights) == 0:
        return None
    
    numerator = sum(value * weight for value, weight in zip(values, weights))
    denominator = sum(weights)
    weighted_average = numerator / denominator

    moe = weighted_average * sqrt(
        # numerator term
        (
            sqrt(
                sum(
                    [
                        ((v * w) * sqrt((we / w) ** 2 + (e / v) ** 2)) ** 2
                        for v, e, w, we in zip(
                            values, value_moes, weights, weight_moes
                        )
                    ]
                )
            )
            / numerator
        )
        ** 2
        # denominator term
        + (sqrt(sum([we**2 for we in weight_moes])) / denominator) ** 2
    )

    return round(moe, 2)
