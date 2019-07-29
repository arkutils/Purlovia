import re
import unicodedata


def get_valid_filename(value: str) -> str:
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'(?u)[^-\w.]', '', value)
    return value
