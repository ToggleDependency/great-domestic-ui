from directory_api_client.client import api_client
import pytest
import requests
import requests_mock

from contact import constants, forms, views


routing_steps = [step for step, _ in views.RoutingFormView.form_list]


@pytest.fixture
def domestic_data(captcha_stub):
    return {
        'given_name': 'Test',
        'family_name': 'Example',
        'email': 'test@example.com',
        'company_type': 'LIMITED',
        'organisation_name': 'Example corp',
        'postcode': 'ABC123',
        'comment': 'Help please',
        'g-recaptcha-response': captcha_stub,
        'terms_agreed': True,
    }


def test_location_form_routing():
    field = forms.LocationRoutingForm.base_fields['choice']
    # for each of the choices the form supports
    for choice, _ in field.choices:
        # the view supports routing the user to that step
        assert choice in routing_steps


def test_domestic_form_routing():
    field = forms.DomesticRoutingForm.base_fields['choice']
    choices = set(item for item, _ in field.choices)

    # expect these choices to result in a redirect to a new form
    choices_expect_redirect = {
        constants.TRADE_OFFICE,
        constants.EXPORT_ADVICE,
        constants.FINANCE,
        constants.EUEXIT,
        constants.EVENTS,
        constants.DSO,
        constants.OTHER,
    }
    mapping = views.RoutingFormView.redirect_mapping[constants.DOMESTIC]

    for choice in choices_expect_redirect:
        assert choice in choices
        assert choice in mapping
        assert choice not in routing_steps

    choices_expect_next_step = (constants.GREAT_SERVICES,)
    for choice in choices_expect_next_step:
        assert choice in choices
        assert choice not in mapping
        assert choice in routing_steps

    expected_choice_count = (
        len(choices_expect_next_step) + len(choices_expect_redirect)
    )

    assert expected_choice_count == len(choices)


def test_great_services_form_routing():
    field = forms.GreatServicesRoutingForm.base_fields['choice']
    choices = set(item for item, _ in field.choices)

    choices_expect_redirect = {
        constants.OTHER,
    }
    mapping = views.RoutingFormView.redirect_mapping[constants.GREAT_SERVICES]

    for choice in choices_expect_redirect:
        assert choice in choices
        assert choice in mapping
        assert choice not in routing_steps

    choices_expect_next_step = {
        constants.EXPORT_OPPORTUNITIES,
        constants.GREAT_ACCOUNT,
    }
    for choice in choices_expect_next_step:
        assert choice in choices
        assert choice not in mapping
        assert choice in routing_steps

    expected_choice_count = (
        len(choices_expect_next_step) + len(choices_expect_redirect)
    )

    assert expected_choice_count == len(choices)


def test_export_oppotunities_form_routing():
    field = forms.ExportOpportunitiesRoutingForm.base_fields['choice']

    mapping = (
        views.RoutingFormView.redirect_mapping[constants.EXPORT_OPPORTUNITIES]
    )

    for choice, _ in field.choices:
        assert choice in mapping
        assert choice not in routing_steps


def test_great_account_form_routing():
    # expect these to route to a FAQ page
    pass


def test_international_form_routing():
    field = forms.InternationalRoutingForm.base_fields['choice']
    mapping = views.RoutingFormView.redirect_mapping[constants.INTERNATIONAL]
    for choice, _ in field.choices:
        assert choice in mapping
        assert choice not in routing_steps


def test_short_notify_form_serialize_data(domestic_data):
    form = forms.ShortNotifyForm(data=domestic_data)

    assert form.is_valid()

    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )
    office_details = {'name': 'Some Office', 'email': 'foo@example.com'}
    with requests_mock.mock() as mock:
        mock.get(url, json=office_details)
        data = form.serialized_data

    assert data == {
        'given_name': 'Test',
        'family_name': 'Example',
        'email': 'test@example.com',
        'company_type': 'LIMITED',
        'company_type_other': '',
        'organisation_name': 'Example corp',
        'postcode': 'ABC123',
        'comment': 'Help please',
        'dit_regional_office_name': 'Some Office',
        'dit_regional_office_email': 'foo@example.com',
    }


def test_short_zendesk_form_serialize_data(domestic_data):
    form = forms.ShortZendeskForm(data=domestic_data)

    assert form.is_valid()

    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )
    office_details = {'name': 'Some Office', 'email': 'foo@example.com'}
    with requests_mock.mock() as mock:
        mock.get(url, json=office_details)
        data = form.serialized_data

    assert data == {
        'given_name': 'Test',
        'family_name': 'Example',
        'email': 'test@example.com',
        'company_type': 'LIMITED',
        'company_type_other': '',
        'organisation_name': 'Example corp',
        'postcode': 'ABC123',
        'comment': 'Help please',
    }
    assert form.full_name == 'Test Example'


def test_domestic_contact_form_serialize_data_office_lookup_error(
    domestic_data
):
    form = forms.ShortNotifyForm(data=domestic_data)

    assert form.is_valid()

    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )
    with requests_mock.mock() as mock:
        mock.get(url, exc=requests.exceptions.ConnectTimeout)
        data = form.serialized_data

    assert data['dit_regional_office_name'] == ''
    assert data['dit_regional_office_email'] == ''


def test_domestic_contact_form_serialize_data_office_lookup_not_found(
    domestic_data
):
    form = forms.ShortNotifyForm(data=domestic_data)

    assert form.is_valid()

    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )
    with requests_mock.mock() as mock:
        mock.get(url, status_code=404)
        data = form.serialized_data

    assert data['dit_regional_office_name'] == ''
    assert data['dit_regional_office_email'] == ''


def test_feedback_form_serialize_data(captcha_stub):
    form = forms.FeedbackForm(
        data={
            'name': 'Test Example',
            'email': 'test@example.com',
            'comment': 'Help please',
            'g-recaptcha-response': captcha_stub,
            'terms_agreed': True,
        }
    )

    assert form.is_valid()
    assert form.serialized_data == {
        'name': 'Test Example',
        'email': 'test@example.com',
        'comment': 'Help please',
    }
    assert form.full_name == 'Test Example'


@pytest.mark.parametrize('form_class,value', (
    (forms.DomesticRoutingForm, True),
    (forms.DomesticRoutingForm, False),
    (forms.InternationalRoutingForm, True),
    (forms.InternationalRoutingForm, False),
))
def test_routing_forms_feature_flag(form_class, value, feature_flags):
    feature_flags['EU_EXIT_FORMS_ON'] = value

    choices = form_class().fields['choice'].choices

    assert any(value == constants.EUEXIT for value, label in choices) is value


def test_office_finder_unknown_postcode():
    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )

    form = forms.OfficeFinderForm(data={'postcode': 'ABC123'})

    with requests_mock.mock() as mock:
        mock.get(url, status_code=404)
        assert form.is_valid() is False

    assert form.errors['postcode'] == [form.MESSAGE_NOT_FOUND]


def test_office_finder_known_postcode():
    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )
    office_details = {'field': 'value'}

    form = forms.OfficeFinderForm(data={'postcode': 'ABC123'})

    with requests_mock.mock() as mock:
        mock.get(url, json=office_details)
        assert form.is_valid() is True

    assert form.office_details == {'field': 'value'}
