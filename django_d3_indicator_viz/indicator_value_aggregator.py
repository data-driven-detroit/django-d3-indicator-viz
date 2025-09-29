from abc import ABC, abstractmethod
from math import sqrt

class aggregation_result:
    '''
    Class to hold aggregation results.
    '''

    # The aggregated value.
    value = None

    # The number of values that were considered for aggregation.
    values_considered = 0

    # The number of values that were aggregated.
    values_aggregated = 0

class IndicatorValueAggregator(ABC):
    '''
    Class to aggregate indicator values.
    Provides functions to aggregate different types of indicator values.
    See Section 8 of the ACS General Handbook for more information on the calculations.
    https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_general_handbook_2020.pdf
    '''

    def aggregate_count_values(self, count_values):
        '''
        Aggregates count values.
        '''
        result = aggregation_result()
        result.values_considered = len(count_values)
        result.values_aggregated = len([value for value in count_values if value is not None])
        valid_values = [value for value in count_values if value is not None]
        result.value = sum(valid_values)
        
        return result

    def aggregate_count_moe_values(self, moe_values):
        '''
        Aggregates count margin of error values.
        '''
        result = aggregation_result()
        result.values_considered = len(moe_values)
        result.values_aggregated = len([value for value in moe_values if value is not None])
        valid_moe_values = [value for value in moe_values if value is not None]
        result.value = round(sqrt(sum(moe ** 2 for moe in valid_moe_values)), 2)

        return result

    def aggregate_percentage_values(self, count_values, universe_values):
        '''
        Aggregates percentage values.
        '''
        result = aggregation_result()
        result.values_considered = len(count_values)
        result.values_aggregated = len([value for value in count_values if value is not None 
                                        and universe_values[count_values.index(value)] is not None])
        valid_count_values = [value for value in count_values if value is not None 
                                and universe_values[count_values.index(value)] is not None]
        valid_universe_values = [value for value in universe_values if value is not None 
                                    and count_values[universe_values.index(value)] is not None]
        if sum(valid_universe_values) == 0:
            result.value = None
        else:
            result.value = round(sum(valid_count_values) / sum(valid_universe_values) * 100, 2)

        return result

    def aggregate_percentage_moe_values(self, count_values, universe_values, count_moe_values, universe_moe_values):
        '''
        Aggregates percentage margin of error values.
        '''
        result = aggregation_result()
        result.values_considered = len(count_values)
        result.values_aggregated = len([value for value in count_values if value is not None 
                                        and universe_values[count_values.index(value)] is not None 
                                        and count_moe_values[count_values.index(value)] is not None 
                                        and universe_moe_values[count_values.index(value)] is not None])
        aggregate_percentage_value = self.aggregate_percentage_values(count_values, universe_values).value
        valid_universe_values = [value for value in universe_values if value is not None 
                                and count_values[universe_values.index(value)] is not None]
        if aggregate_percentage_value is None or sum(valid_universe_values) == 0:
            result.value = None
        else:
            valid_count_moe_values = [value for value in count_moe_values if value is not None 
                                and universe_moe_values[count_moe_values.index(value)] is not None]
            valid_universe_moe_values = [value for value in universe_moe_values if value is not None 
                                    and count_moe_values[universe_moe_values.index(value)] is not None]
            count_moe_sum_squares = sum(moe ** 2 for moe in valid_count_moe_values)
            universe_moe_sum_squares = sum(moe ** 2 for moe in valid_universe_moe_values)
            
        
            result.value = round(sqrt((count_moe_sum_squares - (aggregate_percentage_value / 100) ** 2 * universe_moe_sum_squares)) / sum(valid_universe_values) * 100, 2)

        return result

    def aggregate_median_values(self, median_values, universe_values):
        '''
        Aggregates median values.
        '''
        return self.__aggregate_weighted_averages(median_values, universe_values)

    def aggregate_median_moe_values(self, median_values, universe_values, median_moe_values, universe_moe_values):
        '''
        Aggregates median margin of error values.
        '''
        return self.__aggregate_weighted_average_moes(median_values, universe_values, median_moe_values, universe_moe_values)

    def aggregate_average_values(self, average_values, universe_values):
        '''
        Aggregates average values.
        '''
        return self.__aggregate_weighted_averages(average_values, universe_values)

    def aggregate_average_moe_values(self, average_values, universe_values, average_moe_values, universe_moe_values):
        '''
        Aggregates average margin of error values.
        '''
        return self.__aggregate_weighted_average_moes(average_values, universe_values, average_moe_values, universe_moe_values)

    def aggregate_rate_values(self, count_values, universe_values, rate_per):
        '''
        Aggregates rate values.
        '''
        result = aggregation_result()
        result.values_considered = len(count_values)
        result.values_aggregated = len([value for value in count_values if value is not None 
                                        and universe_values[count_values.index(value)] is not None])
        valid_count_values = [value for value in count_values if value is not None
                                and universe_values[count_values.index(value)] is not None]
        valid_universe_values = [value for value in universe_values if value is not None
                                and count_values[universe_values.index(value)] is not None]
        if sum(valid_universe_values) == 0:
            result.value = None
        else:
            result.value = round(sum(valid_count_values) / sum(valid_universe_values) * rate_per, 2)

        return result

    def aggregate_rate_moe_values(self, count_values, universe_values, count_moe_values, universe_moe_values, rate_per):
        '''
        Aggregates rate margin of error values.
        '''
        result = aggregation_result()
        result.values_considered = len(count_values)
        result.values_aggregated = len([value for value in count_values if value is not None 
                                        and universe_values[count_values.index(value)] is not None
                                        and count_moe_values[count_values.index(value)] is not None
                                        and universe_moe_values[count_values.index(value)] is not None])
        valid_count_values = [value for value in count_values if value is not None
                                and universe_values[count_values.index(value)] is not None
                                and count_moe_values[count_values.index(value)] is not None
                                and universe_moe_values[count_values.index(value)] is not None]
        valid_universe_values = [value for value in universe_values if value is not None
                                and count_values[universe_values.index(value)] is not None
                                and count_moe_values[universe_values.index(value)] is not None
                                and universe_moe_values[universe_values.index(value)] is not None]
        valid_count_moe_values = [value for value in count_moe_values if value is not None
                                and universe_moe_values[count_moe_values.index(value)] is not None
                                and count_values[count_moe_values.index(value)] is not None
                                and universe_values[count_moe_values.index(value)] is not None]
        valid_universe_moe_values = [value for value in universe_moe_values if value is not None
                                and count_moe_values[universe_moe_values.index(value)] is not None
                                and count_values[universe_moe_values.index(value)] is not None
                                and universe_values[universe_moe_values.index(value)] is not None]
        if sum(valid_universe_values) == 0:
            result.value = None
        else:
            count_moe = self.aggregate_count_moe_values(valid_count_moe_values).value
            universe_moe = self.aggregate_count_moe_values(valid_universe_moe_values).value
            aggregate_rate = self.aggregate_rate_values(valid_count_values, valid_universe_values, rate_per).value
            if count_moe is None or universe_moe is None or aggregate_rate is None:
                result.value = None
            else:
                result.value = round(
                    sqrt(count_moe ** 2 + (aggregate_rate ** 2 * universe_moe ** 2))
                    /
                    sum(valid_universe_values), 2
                )

        return result

    @abstractmethod
    def aggregate_index_values(self, index_values):
        pass

    @abstractmethod
    def aggregate_index_moe_values(self, index_values, index_moe_values):
        pass

    def __aggregate_weighted_averages(self, values, weights):
        '''
        Aggregates weighted average values.
        '''
        result = aggregation_result()
        result.values_considered = len(values)
        result.values_aggregated = len([value for value in values if value is not None 
                                        and weights[values.index(value)] is not None])
        valid_values = [value for value in values if value is not None 
                        and weights[values.index(value)] is not None]
        valid_weights = [weight for weight in weights if weight is not None
                        and values[weights.index(weight)] is not None]
        if sum(valid_weights) == 0:
            result.value = None
        else:
            weighted_sum = sum(value * weight for value, weight in zip(valid_values, valid_weights))
            total_weight = sum(valid_weights)
            result.value = round(weighted_sum / total_weight, 2)
        
        return result

    def __aggregate_weighted_average_moes(self, values, weights, value_moes, weight_moes):
        '''
        Aggregates weighted average margin of error values.
        '''
        result = aggregation_result()
        result.values_considered = len(values)
        result.values_aggregated = len([value for value in values if value is not None 
                                        and weights[values.index(value)] is not None 
                                        and value_moes[values.index(value)] is not None 
                                        and weight_moes[values.index(value)] is not None])
        valid_values = [value for value in values if value is not None
                        and weights[values.index(value)] is not None
                        and value_moes[values.index(value)] is not None
                        and weight_moes[values.index(value)] is not None]
        valid_weights = [weight for weight in weights if weight is not None
                        and values[weights.index(weight)] is not None
                        and value_moes[weights.index(weight)] is not None
                        and weight_moes[weights.index(weight)] is not None]
        valid_value_moes = [moe for moe in value_moes if moe is not None
                        and values[value_moes.index(moe)] is not None
                        and weights[value_moes.index(moe)] is not None
                        and weight_moes[value_moes.index(moe)] is not None]
        valid_weight_moes = [moe for moe in weight_moes if moe is not None
                        and values[weight_moes.index(moe)] is not None
                        and weights[weight_moes.index(moe)] is not None
                        and value_moes[weight_moes.index(moe)] is not None]
        if sum(valid_weights) == 0:
            return None
        else:
            numerator = sum(value * weight for value, weight in zip(valid_values, valid_weights))
            denominator = sum(valid_weights)
            weighted_average = numerator / denominator
            moe = weighted_average * sqrt(
                # numerator term
                (
                    sqrt(
                        sum(
                            [
                                ((v * w) * sqrt((we / w) ** 2 + (e / v) ** 2)) ** 2
                                for v, e, w, we in zip(
                                    valid_values, valid_value_moes, valid_weights, valid_weight_moes
                                )
                            ]
                        )
                    )
                    / numerator
                )
                ** 2
                # denominator term
                + (sqrt(sum([we**2 for we in valid_weight_moes])) / denominator) ** 2
            )
            result.value = round(moe, 2)

        return result
