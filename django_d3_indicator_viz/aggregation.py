def build_indicator_values_dict_list(indicator_values):
    return [
        {
            "location_id": iv.location_id,
            "indicator_id": iv.indicator_id,
            "source_id": iv.source_id,
            "filter_option_id": iv.filter_option_id,
            "start_date": iv.start_date,
            "end_date": iv.end_date,
            "value": iv.value,
            "value_moe": iv.value_moe,
            "count": iv.count,
            "count_moe": iv.count_moe,
            "universe": iv.universe,
            "universe_moe": iv.universe_moe,
            "active_data": iv.active_data,
        }
        for iv in indicator_values
    ]


def aggregate_indicator_values(
    custom_location, data_visual, indicator_values, indicator_value_aggregator,
    source_id=None,
):
    grouped_values = {}
    for iv in build_indicator_values_dict_list(indicator_values):
        if iv["indicator_id"] != data_visual.indicator.id:
            continue
        key = (iv["filter_option_id"], iv["start_date"])
        if key not in grouped_values:
            grouped_values[key] = []
        grouped_values[key].append(iv)
    aggregated_values = []
    for (filter_option_id, start_date), ivs in grouped_values.items():
        aggregated_value = aggregate_indicator_value_set(
            custom_location, data_visual, ivs, indicator_value_aggregator,
            source_id=source_id,
        )
        aggregated_values.append(aggregated_value)
    return aggregated_values


def aggregate_indicator_value_set(
    custom_location, data_visual, indicator_values, indicator_value_aggregator,
    source_id=None,
):
    aggregate_value = {
        "location_id": str(custom_location.id),
        "indicator_id": data_visual.indicator.id,
        "source_id": source_id or (
            indicator_values[0]["source_id"] if indicator_values else None
        ),
        "filter_option_id": (
            indicator_values[0]["filter_option_id"]
            if indicator_values
            else None
        ),
        "start_date": (
            indicator_values[0]["start_date"] if indicator_values else None
        ),
        "end_date": (
            indicator_values[0]["end_date"] if indicator_values else None
        ),
        "count": indicator_value_aggregator.aggregate_count_values(
            [iv["count"] for iv in indicator_values]
        ).value,
        "count_moe": indicator_value_aggregator.aggregate_count_moe_values(
            [iv["count_moe"] for iv in indicator_values]
        ).value,
        "universe": indicator_value_aggregator.aggregate_count_values(
            [iv["universe"] for iv in indicator_values]
        ).value,
        "universe_moe": indicator_value_aggregator.aggregate_count_moe_values(
            [iv["universe_moe"] for iv in indicator_values]
        ).value,
        "value": None,
        "value_moe": None,
        "values_considered": None,
        "values_aggregated": None,
        "active_data": (
            indicator_values[0]["active_data"] if indicator_values else True
        ),
    }

    if data_visual.indicator.indicator_type == "count":
        aggregate_value_result = (
            indicator_value_aggregator.aggregate_count_values(
                [iv["count"] for iv in indicator_values]
            )
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_count_moe_values(
                [iv["count_moe"] for iv in indicator_values]
            )
        )
        aggregate_value["value"] = aggregate_value_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_value_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_value_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "percentage":
        aggregate_value_result = (
            indicator_value_aggregator.aggregate_percentage_values(
                [iv["count"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
            )
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_percentage_moe_values(
                [iv["count"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["count_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
            )
        )
        aggregate_value["value"] = aggregate_value_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_value_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_value_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "median":
        aggregate_value_result = (
            indicator_value_aggregator.aggregate_median_values(
                [iv["value"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
            )
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_median_moe_values(
                [iv["value"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["value_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
            )
        )
        aggregate_value["value"] = aggregate_value_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_value_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_value_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "average":
        aggregate_result = indicator_value_aggregator.aggregate_average_values(
            [iv["value"] for iv in indicator_values],
            [iv["universe"] for iv in indicator_values],
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_average_moe_values(
                [iv["value"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["value_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
            )
        )
        aggregate_value["value"] = aggregate_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "rate":
        aggregate_result = indicator_value_aggregator.aggregate_rate_values(
            [iv["count"] for iv in indicator_values],
            [iv["universe"] for iv in indicator_values],
            data_visual.indicator.rate_per,
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_rate_moe_values(
                [iv["count"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["count_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
                data_visual.indicator.rate_per,
            )
        )
        aggregate_value["value"] = aggregate_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "index":
        # index aggregation not supported for custom locations in SDC
        pass

    return aggregate_value
