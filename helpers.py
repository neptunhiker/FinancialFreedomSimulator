import math
from typing import List, Union

# def validate_positive_number(positive_number: Union[float, int]) -> None:
#     """
#     Validate whether the given argument is a positive number
#     :param positive_number: A number to be validated
#     :return: None
#     """
#     if math.isnan(positive_number):
#         raise ValueError("The given argument must be a valid number.")
#     if positive_number <= 0:
#         raise ValueError("The given argument must be a positive number.")
#


def validate_positive_numbers(positive_numbers: List[Union[float, int]]) -> None:
    """
    Validate whether the given argument is a positive number
    :param positive_numbers: A list of numbers to be validated
    :return: None
    """
    if not positive_numbers:
        raise ValueError("The given list to validate has to contain entries. It is currently an empty list.")
    for positive_number in positive_numbers:
        if math.isnan(positive_number):
            raise ValueError("The given argument must be a valid number.")
        if positive_number <= 0:
            raise ValueError("The given argument must be a positive number.")

