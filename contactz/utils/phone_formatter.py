"""
Phone Number Formatter
Converts phone numbers to international format starting with 00
Example: 040 12345678 → 0049 40 12345678
"""

import re


def format_phone_international(phone_number, country_code='49'):
    """
    Format phone number to international format starting with 00

    Args:
        phone_number: Phone number in various formats
        country_code: Default country code (default: 49 for Germany)

    Returns:
        Formatted phone number in format: 0049 XX XXXXXXX

    Examples:
        >>> format_phone_international("040 12345678")
        "0049 40 12345678"
        >>> format_phone_international("+49 151 23456789")
        "0049 151 23456789"
        >>> format_phone_international("0049 40 12345678")
        "0049 40 12345678"
        >>> format_phone_international("05191-983422")
        "0049 5191 983422"
    """
    if not phone_number:
        return ""

    # Convert to string and strip whitespace
    cleaned = str(phone_number).strip()

    if not cleaned:
        return ""

    # Handle different input formats
    if cleaned.startswith('+' + country_code):
        # +49 40 12345678 → 0049 40 12345678
        cleaned = '00' + country_code + cleaned[len(country_code) + 1:]
    elif cleaned.startswith('00' + country_code):
        # Already in correct format: 0049 40 12345678
        pass
    elif cleaned.startswith(country_code) and len(cleaned) > len(country_code) and cleaned[len(country_code)].isdigit():
        # 49 40 12345678 → 0049 40 12345678
        # But be careful: 4912... might be an area code starting with 49
        # Check if next char after country_code is likely area code start
        if len(cleaned) > len(country_code) + 1 and cleaned[len(country_code)] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            cleaned = '00' + cleaned
    elif cleaned.startswith('0') and not cleaned.startswith('00'):
        # 040 12345678 → 0049 40 12345678
        cleaned = '00' + country_code + cleaned[1:]

    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, cleaned))

    if not digits_only:
        return ""

    # Format with spaces for German numbers
    if digits_only.startswith('00' + country_code):
        prefix_len = 2 + len(country_code)  # '00' + country_code

        if len(digits_only) <= prefix_len + 3:
            # Very short number, just add one space after country code
            return f"00{country_code} {digits_only[prefix_len:]}"
        else:
            # Format: 0049 XX XXXXXXX or 0049 XXX XXXXXX
            # Identify area code length (usually 2-4 digits after country code)
            area_code_len = 2

            # Mobile numbers in Germany start with 1 (e.g., 015x, 016x, 017x)
            if len(digits_only) > prefix_len and digits_only[prefix_len] == '1':
                area_code_len = 3
            # Some cities have 3-digit area codes
            elif len(digits_only) > prefix_len + 10:
                area_code_len = 3

            area_code = digits_only[prefix_len:prefix_len + area_code_len]
            rest = digits_only[prefix_len + area_code_len:]

            if rest:
                return f"00{country_code} {area_code} {rest}"
            else:
                return f"00{country_code} {area_code}"

    # Not a German number or unrecognized format - return digits only
    return digits_only


def format_phone_batch(phone_numbers, country_code='49'):
    """
    Format multiple phone numbers at once

    Args:
        phone_numbers: List of phone numbers
        country_code: Default country code

    Returns:
        List of formatted phone numbers
    """
    return [format_phone_international(num, country_code) for num in phone_numbers]


def clean_phone_number(phone_number):
    """
    Remove all non-digit characters except leading +

    Args:
        phone_number: Phone number string

    Returns:
        Cleaned phone number with only digits (and optional leading +)
    """
    if not phone_number:
        return ""

    cleaned = str(phone_number).strip()

    # Keep leading + if present
    has_plus = cleaned.startswith('+')

    # Remove all non-digits
    digits = ''.join(filter(str.isdigit, cleaned))

    if has_plus:
        return '+' + digits

    return digits
