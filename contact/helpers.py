from core.helpers import retrieve_regional_offices


def retrieve_regional_office(postcode):
    all_offices = retrieve_regional_offices(postcode)
    regional_office = [office for office in all_offices if office['is_match']]
    return regional_office[0] if regional_office else None


def extract_regional_office_details(all_offices):
    matches = [office for office in all_offices if office['is_match']]
    formatted_office_details = format_office_details(matches)
    return formatted_office_details[0] if formatted_office_details else None


def extract_other_offices_details(all_offices):
    other_offices = [
        office for office in all_offices if not office['is_match']
    ]
    return format_office_details(other_offices)


def format_office_details(office_list):
    offices = []
    for office in office_list:
        address = office['address_street'].split(', ')
        address.append(office['address_city'])
        address.append(office['address_postcode'])
        office = {'address': '\n'.join(address), **office}
        offices.append(office)
    return offices if len(offices) > 0 else None
