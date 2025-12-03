from __future__ import absolute_import
from django import template
from django.utils.safestring import mark_safe


register = template.Library()


COMPARISON_PHRASES = [
    (8, ("less than 10 percent", "of")),
    (13, ("about 10 percent", "of")),
    (17, ("less than a fifth", "of")),
    (23, ("about one-fifth", "of")),
    (30, ("about one-quarter", "of")),
    (37, ("about one-third", "of")),
    (45, ("about two-fifths", "of")),
    (56, ("about half", "")),
    (64, ("about three-fifths", "of")),
    (72, ("about two-thirds", "of")),
    (78, ("about three-quarters", "of")),
    (86, ("about 80 percent", "of")),
    (94, ("about 90 percent", "of")),
    (98, ("a little less", "than")),
    (103, ("about the same as", "")),
    (107, ("a little higher", "than")),
    (115, ("about 10 percent higher", "than")),
    (122, ("about 20 percent higher", "than")),
    (128, ("about 25 percent higher", "than")),
    (135, ("about 1.3 times", "")),
    (145, ("about 1.4 times", "")),
    (161, ("about 1.5 times", "")),
    (180, ("more than 1.5 times", "")),
    (195, ("nearly double", "")),
    (206, ("about double", "")),
    (float("inf"), ("more than double", "")),
]


@register.filter
def comparison_index_phrase(value):
    """
    Each stat on the profile page can have nation-, state- and county-level
    values, indexed to 100 for comparisons (that is, expressed as a percentage
    of that statistic's value for the profile geography). That index value can
    be passed into this template filter to generate a comparative phrase.

    COMPARISON_PHRASES defines the comparative phrases. The first entry of the
    tuple shows the uppper_bound of the range. The loop walks through the phrases
    from smallest to largest and stops on the first phrase where the value is
    below the upper boundary.

    For example, the effective range of index values that return the phrase
    "about half" would be 45 to 55. (eg. 47 is less than 45 and greater than 56).
    """

    for upper_bound, phrase_parts in COMPARISON_PHRASES:
        if value < upper_bound:
            phrase = f"<strong>{phrase_parts[0]}</strong> {phrase_parts[1]}"
            return mark_safe(phrase)


@register.filter
def stat_type_to_number_noun(stat_type):
    if stat_type == "dollar":
        return "amount"
    elif stat_type == "percentage":
        return "rate"
    return "figure"
