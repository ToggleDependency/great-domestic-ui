from unittest import mock

from directory_api_client.client import api_client
from directory_constants.constants import cms
import pytest
import requests_mock

import django.forms
from django.conf import settings
from django.urls import reverse
from django.views.generic import TemplateView

from contact import constants, forms, views
from core.tests.helpers import create_response


def build_wizard_url(step):
    return reverse('triage-wizard', kwargs={'step': step})


class ChoiceForm(django.forms.Form):
    choice = django.forms.CharField()


@pytest.fixture()
def office_details():
    return {
        'region_id': 'east_midlands',
        'name': 'DIT East Midlands',
        'address_street': (
            'The International Trade Centre, '
            '5 Merus Court, '
            'Meridian Business Park'
        ),
        'address_city': 'Leicester',
        'address_postcode': 'LE19 1RJ',
        'email': 'test+east_midlands@examoke.com',
        'phone': '0345 052 4001',
        'phone_other': '',
        'phone_other_comment': '',
        'website': None
    }


@pytest.fixture(autouse=True)
def company_profile(authed_client):
    path = 'core.mixins.PrepopulateFormMixin.company_profile'
    stub = mock.patch(
        path,
        new_callable=mock.PropertyMock,
        return_value={
            'number': 1234567,
            'name': 'Example corp',
            'postal_code': 'Foo Bar',
            'sectors': ['AEROSPACE'],
            'employees': '1-10',
            'mobile_number': '07171771717',
            'postal_full_name': 'Foo Example',
            'address_line_1': '123 Street',
            'address_line_2': 'Near Fake Town',
            'country': 'FRANCE',
            'locality': 'Paris',
            'website': 'http://www.example.com',
        }
    )
    yield stub.start()
    stub.stop()


@pytest.fixture
def domestic_form_data(captcha_stub):
    return {
        'given_name': 'Test',
        'family_name': 'Example',
        'email': 'test@example.com',
        'company_type': 'LIMITED',
        'organisation_name': 'Example corp',
        'postcode': '**** ***',
        'comment': 'Help please',
        'g-recaptcha-response': captcha_stub,
        'terms_agreed': True,
    }


@pytest.mark.parametrize('current_step,choice,expected_url', (
    # location step routing
    (
        constants.LOCATION,
        constants.DOMESTIC,
        build_wizard_url(constants.DOMESTIC),
    ),
    (
        constants.LOCATION,
        constants.INTERNATIONAL,
        build_wizard_url(constants.INTERNATIONAL),
    ),
    # domestic step routing
    (
        constants.DOMESTIC,
        constants.TRADE_OFFICE,
        views.LazyOfficeFinderURL(),
    ),
    (
        constants.DOMESTIC,
        constants.EXPORT_ADVICE,
        reverse(
            'contact-us-export-advice',
            kwargs={'step': 'comment'}
        ),
    ),
    (
        constants.DOMESTIC,
        constants.FINANCE,
        reverse(
            'uk-export-finance-lead-generation-form',
            kwargs={'step': 'contact'},
        )
    ),
    (
        constants.DOMESTIC,
        constants.EUEXIT,
        reverse('eu-exit-domestic-contact-form'),
    ),
    (
        constants.DOMESTIC,
        constants.EVENTS,
        reverse('contact-us-events-form'),
    ),
    (
        constants.DOMESTIC,
        constants.DSO,
        reverse('contact-us-dso-form')
    ),
    (
        constants.DOMESTIC,
        constants.OTHER,
        reverse('contact-us-domestic')
    ),
    # great services guidance routing
    (
        constants.GREAT_SERVICES,
        constants.EXPORT_OPPORTUNITIES,
        build_wizard_url(constants.EXPORT_OPPORTUNITIES),
    ),
    (
        constants.GREAT_SERVICES,
        constants.GREAT_ACCOUNT,
        build_wizard_url(constants.GREAT_ACCOUNT),
    ),
    (
        constants.GREAT_SERVICES,
        constants.OTHER,
        reverse('contact-us-domestic'),
    ),
    # great account
    (
        constants.GREAT_ACCOUNT,
        constants.NO_VERIFICATION_EMAIL,
        views.build_great_account_guidance_url(
            cms.EXPORT_READINESS_HELP_MISSING_VERIFY_EMAIL_SLUG
        ),
    ),
    (
        constants.GREAT_ACCOUNT,
        constants.PASSWORD_RESET,
        views.build_great_account_guidance_url(
            cms.EXPORT_READINESS_HELP_PASSWORD_RESET_SLUG
        ),
    ),
    (
        constants.GREAT_ACCOUNT,
        constants.COMPANIES_HOUSE_LOGIN,
        views.build_great_account_guidance_url(
            cms.EXPORT_READINESS_HELP_COMPANIES_HOUSE_LOGIN_SLUG
        ),
    ),
    (
        constants.GREAT_ACCOUNT,
        constants.VERIFICATION_CODE,
        views.build_great_account_guidance_url(
            cms.EXPORT_READINESS_HELP_VERIFICATION_CODE_ENTER_SLUG
        ),
    ),
    (
        constants.GREAT_ACCOUNT,
        constants.NO_VERIFICATION_LETTER,
        views.build_great_account_guidance_url(
            cms.EXPORT_READINESS_HELP_VERIFICATION_CODE_LETTER_SLUG
        )
    ),
    (
        constants.GREAT_ACCOUNT,
        constants.OTHER,
        reverse('contact-us-domestic'),
    ),
    # Export opportunities guidance routing
    (
        constants.EXPORT_OPPORTUNITIES,
        constants.NO_RESPONSE,
        views.build_export_opportunites_guidance_url(
            cms.EXPORT_READINESS_HELP_EXOPP_NO_RESPONSE
        ),
    ),
    (
        constants.EXPORT_OPPORTUNITIES,
        constants.ALERTS,
        views.build_export_opportunites_guidance_url(
            cms.EXPORT_READINESS_HELP_EXOPP_ALERTS_IRRELEVANT_SLUG
        ),
    ),
    (
        constants.EXPORT_OPPORTUNITIES,
        constants.OTHER,
        reverse('contact-us-domestic'),
    ),
    # international routing
    (
        constants.INTERNATIONAL,
        constants.INVESTING,
        settings.INVEST_CONTACT_URL,
    ),
    (
        constants.INTERNATIONAL,
        constants.BUYING,
        settings.FIND_A_SUPPLIER_CONTACT_URL,
    ),
    (
        constants.INTERNATIONAL,
        constants.EUEXIT,
        reverse('eu-exit-international-contact-form'),
    ),
    (
        constants.INTERNATIONAL,
        constants.OTHER,
        reverse('contact-us-international'),
    ),
))
def test_render_next_step(current_step, choice, expected_url):
    form = ChoiceForm(data={'choice': choice})

    view = views.RoutingFormView()
    view.steps = mock.Mock(current=current_step)
    view.storage = mock.Mock()
    view.url_name = 'triage-wizard'
    view.request = mock.Mock()

    assert form.is_valid()
    assert view.render_next_step(form).url == expected_url


@pytest.mark.parametrize('current_step,expected_step', (
    (constants.DOMESTIC, constants.LOCATION),
    (constants.INTERNATIONAL, constants.LOCATION),
    (constants.GREAT_SERVICES, constants.DOMESTIC),
    (constants.GREAT_ACCOUNT, constants.GREAT_SERVICES),
    (constants.EXPORT_OPPORTUNITIES, constants.GREAT_SERVICES),
))
def test_get_previous_step(current_step, expected_step):
    view = views.RoutingFormView()
    view.steps = mock.Mock(current=current_step)
    view.storage = mock.Mock()
    view.url_name = 'triage-wizard'

    assert view.get_prev_step() == expected_step


@pytest.mark.parametrize(
    'url,success_url,view_class,agent_template,user_template,agent_email',
    (
        (
            reverse('contact-us-events-form'),
            reverse('contact-us-events-success'),
            views.EventsFormView,
            settings.CONTACT_EVENTS_AGENT_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_EVENTS_USER_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_EVENTS_AGENT_EMAIL_ADDRESS,
        ),
        (
            reverse('contact-us-dso-form'),
            reverse('contact-us-dso-success'),
            views.DefenceAndSecurityOrganisationFormView,
            settings.CONTACT_DSO_AGENT_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_DSO_USER_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_DSO_AGENT_EMAIL_ADDRESS,
        ),
        (
            reverse('contact-us-international'),
            reverse('contact-us-international-success'),
            views.InternationalFormView,
            settings.CONTACT_INTERNATIONAL_AGENT_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_INTERNATIONAL_USER_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_INTERNATIONAL_AGENT_EMAIL_ADDRESS,
        ),
        (
            reverse('office-finder-contact', kwargs={'postcode': 'FOO'}),
            reverse('contact-us-office-success', kwargs={'postcode': 'FOO'}),
            views.OfficeContactFormView,
            settings.CONTACT_OFFICE_AGENT_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_OFFICE_USER_NOTIFY_TEMPLATE_ID,
            settings.CONTACT_DIT_AGENT_EMAIL_ADDRESS,
        ),
    )
)
def test_notify_form_submit_success(
    client, url, agent_template, user_template, view_class, agent_email,
    success_url
):

    class Form(forms.SerializeDataMixin, django.forms.Form):
        email = django.forms.EmailField()
        save = mock.Mock()

    with mock.patch.object(view_class, 'form_class', Form):
        response = client.post(url, {'email': 'test@example.com'})

    assert response.status_code == 302
    assert response.url == success_url

    assert Form.save.call_count == 2
    assert Form.save.call_args_list == [
        mock.call(
            template_id=agent_template,
            email_address=agent_email,
            form_url=url,
        ),
        mock.call(
            template_id=user_template,
            email_address='test@example.com',
            form_url=url,
        )
    ]


@pytest.mark.parametrize('url,slug', (
    (
        reverse('contact-us-events-success'),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_EVENTS_SLUG,
    ),
    (
        reverse('contact-us-dso-success'),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_DSO_SLUG,
    ),
    (
        reverse('contact-us-export-advice-success'),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_EXPORT_ADVICE_SLUG,
    ),
    (
        reverse('contact-us-feedback-success'),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_FEEDBACK_SLUG,
    ),
    (
        reverse('contact-us-domestic-success'),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_SLUG,
    ),
    (
        reverse('contact-us-international-success'),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_INTERNATIONAL_SLUG,
    ),
    (
        reverse('contact-us-office-success', kwargs={'postcode': 'FOOBAR'}),
        cms.EXPORT_READINESS_CONTACT_US_FORM_SUCCESS_SLUG,
    )
))
@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_success_view_cms(mock_lookup_by_slug, url, slug, client):

    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )

    response = client.get(url)

    assert response.status_code == 200
    assert mock_lookup_by_slug.call_count == 1
    assert mock_lookup_by_slug.call_args == mock.call(
        draft_token=None, language_code='en-gb', slug=slug
    )


@mock.patch('captcha.fields.ReCaptchaField.clean')
@mock.patch('directory_forms_api_client.actions.GovNotifyAction')
@mock.patch('directory_forms_api_client.actions.EmailAction')
@mock.patch('contact.helpers.retrieve_exporting_advice_email')
def test_exporting_from_uk_contact_form_submission(
    mock_retrieve_exporting_advice_email, mock_email_action,
    mock_notify_action, mock_clean, client, captcha_stub, company_profile
):
    company_profile.return_value = None
    mock_retrieve_exporting_advice_email.return_value = 'regional@example.com'

    url_name = 'contact-us-export-advice'
    view_name = 'exporting_advice_form_view'

    response = client.post(
        reverse(url_name, kwargs={'step': 'comment'}),
        {
            view_name + '-current_step': 'comment',
            'comment-comment': 'some comment',
        }
    )
    assert response.status_code == 302

    response = client.post(
        reverse(url_name, kwargs={'step': 'personal'}),
        {
            view_name + '-current_step': 'personal',
            'personal-first_name': 'test',
            'personal-last_name': 'test',
            'personal-position': 'test',
            'personal-email': 'test@example.com',
            'personal-phone': 'test',
        }
    )

    assert response.status_code == 302

    response = client.post(
        reverse(url_name, kwargs={'step': 'business'}),
        {
            view_name + '-current_step': 'business',
            'business-company_type': 'LIMITED',
            'business-companies_house_number': '12345678',
            'business-organisation_name': 'Example corp',
            'business-postcode': '1234',
            'business-industry': 'AEROSPACE',
            'business-turnover': '0-25k',
            'business-employees': '1-10',
            'business-captcha': captcha_stub,
            'business-terms_agreed': True,
        }
    )
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 302
    assert response.url == reverse('contact-us-domestic-success')
    assert mock_clean.call_count == 1
    assert mock_notify_action.call_count == 1
    assert mock_notify_action.call_args == mock.call(
        template_id=settings.CONTACT_EXPORTING_USER_NOTIFY_TEMPLATE_ID,
        email_address='test@example.com',
        form_url='/contact/export-advice/comment/',
    )
    assert mock_notify_action().save.call_count == 1
    assert mock_notify_action().save.call_args == mock.call({
        'comment': 'some comment',
        'first_name': 'test',
        'last_name': 'test',
        'position': 'test',
        'email': 'test@example.com',
        'phone': 'test',
        'company_type': 'LIMITED',
        'companies_house_number': '12345678',
        'company_type_other': '',
        'organisation_name': 'Example corp',
        'postcode': '1234',
        'industry': 'AEROSPACE',
        'industry_other': '',
        'turnover': '0-25k',
        'employees': '1-10',
        'ingress_url': None,
    })

    assert mock_email_action.call_count == 1
    assert mock_email_action.call_args == mock.call(
        recipients=['regional@example.com'],
        subject=settings.CONTACT_EXPORTING_AGENT_SUBJECT,
        reply_to=[settings.DEFAULT_FROM_EMAIL],
        form_url='/contact/export-advice/comment/'
    )
    assert mock_email_action().save.call_count == 1
    assert mock_email_action().save.call_args == mock.call({
        'text_body': mock.ANY, 'html_body': mock.ANY
    })

    assert mock_retrieve_exporting_advice_email.call_count == 1
    assert mock_retrieve_exporting_advice_email.call_args == mock.call(
        '1234'
    )


@mock.patch('captcha.fields.ReCaptchaField.clean')
@mock.patch('directory_forms_api_client.actions.GovNotifyAction')
@mock.patch('directory_forms_api_client.actions.EmailAction')
@mock.patch('contact.helpers.retrieve_exporting_advice_email')
def test_exporting_from_uk_contact_form_initial_data_business(
    mock_retrieve_exporting_advice_email, mock_email_action,
    mock_notify_action, mock_clean, client, captcha_stub,
):
    mock_retrieve_exporting_advice_email.return_value = 'regional@example.com'

    url_name = 'contact-us-export-advice'

    response_one = client.get(reverse(url_name, kwargs={'step': 'personal'}))

    assert response_one.context_data['form'].initial == {
        'email': 'test@foo.com',
        'phone': '07171771717',
        'first_name': 'Foo',
        'last_name': 'Example',
    }

    response_two = client.get(reverse(url_name, kwargs={'step': 'business'}))

    assert response_two.context_data['form'].initial == {
        'company_type': forms.LIMITED,
        'companies_house_number': 1234567,
        'organisation_name': 'Example corp',
        'postcode': 'Foo Bar',
        'industry': 'AEROSPACE',
        'employees': '1-10',
    }


@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_guidance_view_cms_retrieval(mock_lookup_by_slug, client):
    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )

    url = reverse(
        'contact-us-export-opportunities-guidance', kwargs={'slug': 'the-slug'}
    )

    response = client.get(url)

    assert response.status_code == 200
    assert mock_lookup_by_slug.call_count == 1
    assert mock_lookup_by_slug.call_args == mock.call(
        draft_token=None, language_code='en-gb', slug='the-slug'
    )


@pytest.mark.parametrize(
    'url,success_url,view_class,subject',
    (
        (
            reverse('contact-us-domestic'),
            reverse('contact-us-domestic-success'),
            views.DomesticFormView,
            settings.CONTACT_DOMESTIC_ZENDESK_SUBJECT,
        ),
        (
            reverse('contact-us-feedback'),
            reverse('contact-us-feedback-success'),
            views.FeedbackFormView,
            settings.CONTACT_DOMESTIC_ZENDESK_SUBJECT,
        ),
    )
)
def test_zendesk_submit_success(
    client, url, success_url, view_class, subject, settings
):
    class Form(forms.SerializeDataMixin, django.forms.Form):
        email = django.forms.EmailField()
        save = mock.Mock()
        full_name = 'Foo B'

    with mock.patch.object(view_class, 'form_class', Form):
        response = client.post(url, {'email': 'foo@bar.com'})

    assert response.status_code == 302
    assert response.url == success_url

    assert Form.save.call_count == 1
    assert Form.save.call_args == mock.call(
        email_address='foo@bar.com',
        form_url=url,
        full_name='Foo B',
        subject=subject,
        service_name=settings.DIRECTORY_FORMS_API_ZENDESK_SEVICE_NAME
    )


def test_contact_us_feedback_prepopulate(client):
    url = reverse('contact-us-feedback')
    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['form'].initial == {
        'email': 'test@foo.com',
        'name': 'Foo Example',
    }


@pytest.mark.parametrize('url', (
    reverse('contact-us-domestic'),
    reverse('contact-us-dso-form'),
    reverse('contact-us-events-form'),
    reverse('office-finder-contact', kwargs={'postcode': 'FOOBAR'}),
))
def test_contact_us_short_form_prepopualate(client, url):
    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['form'].initial == {
        'email': 'test@foo.com',
        'company_type': forms.LIMITED,
        'organisation_name': 'Example corp',
        'postcode': 'Foo Bar',
        'family_name': 'Example',
        'given_name': 'Foo',
    }


def test_contact_us_international_prepopualate(client):
    url = reverse('contact-us-international')
    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data['form'].initial == {
        'email': 'test@foo.com',
        'organisation_name': 'Example corp',
        'country_name': 'FRANCE',
        'city': 'Paris',
        'family_name': 'Example',
        'given_name': 'Foo'
    }


class IngressURLView(views.IngressURLMixin, TemplateView):

    template_name = 'core/about.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'ingress_url': self.ingress_url,
        }


def test_form_ingress_url_mixin_set_if_http_referer(rf, client):
    request = rf.get('/foo/bar/', HTTP_REFERER='http://referer.com')
    request.session = client.session
    response = IngressURLView.as_view()(request)

    assert response.context_data == {
        'ingress_url': 'http://referer.com',
    }


def test_form_ingress_url_mixin_not_overrite(rf, client):
    session = client.session
    request_one = rf.get('/foo/bar/a/', HTTP_REFERER='http://referer-a.com')
    request_one.session = session
    IngressURLView.as_view()(request_one)

    request_two = rf.get('/foo/bar/b/', HTTP_REFERER='http://referer-b.com')
    request_two.session = session
    response = IngressURLView.as_view()(request_two)

    assert response.context_data == {
        'ingress_url': 'http://referer-a.com',
    }


def test_form_ingress_url_referer_header_missing(rf, client):
    request = rf.get('/foo/bar/')
    request.session = client.session
    response = IngressURLView.as_view()(request)

    assert response.context_data == {
        'ingress_url': None,
    }


success_urls = (
    reverse('contact-us-events-success'),
    reverse('contact-us-dso-success'),
    reverse('contact-us-export-advice-success'),
    reverse('contact-us-feedback-success'),
    reverse('contact-us-domestic-success'),
    reverse('contact-us-international-success'),
)


@pytest.mark.parametrize('url', success_urls)
@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
@mock.patch('contact.views.IngressURLMixin.clear_ingress_url')
def test_ingress_url_cleared_on_success(
    mock_clear_ingress_url, mock_lookup_by_slug, url, client, rf
):
    mock_clear_ingress_url.return_value = None
    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )
    # given the ingress url is set
    client.get(
        reverse('contact-us-routing-form', kwargs={'step': 'location'}),
        HTTP_REFERER='http://testserver.com/foo/',
        HTTP_HOST='testserver.com'
    )

    # when the success page is viewed
    response = client.get(url, HTTP_HOST='testserver.com')

    # then the referer is exposed to the template
    assert response.context_data['next_url'] == 'http://testserver.com/foo/'
    assert response.status_code == 200
    # and the ingress url is cleared
    assert mock_clear_ingress_url.call_count == 1


@pytest.mark.parametrize('url', success_urls)
@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
@mock.patch('contact.views.IngressURLMixin.clear_ingress_url')
def test_external_ingress_url_not_used_on_success(
    mock_clear_ingress_url, mock_lookup_by_slug, url, client
):
    mock_clear_ingress_url.return_value = None
    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )
    # given the ingress url is set
    client.get(
        reverse('contact-us-routing-form', kwargs={'step': 'location'}),
        HTTP_REFERER='http://external.com/foo/',
        HTTP_HOST='testserver.com'
    )

    # when the success page is viewed
    response = client.get(url, HTTP_HOST='testserver.com')

    # then the referer is not exposed to the template
    assert response.context_data['next_url'] == '/'
    assert response.status_code == 200


@pytest.mark.parametrize('url', success_urls)
@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
@mock.patch('contact.views.IngressURLMixin.clear_ingress_url')
def test_ingress_url_not_set_on_success(
    mock_clear_ingress_url, mock_lookup_by_slug, url, client
):
    mock_clear_ingress_url.return_value = None
    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )
    # when the success page is viewed and there is no referer set yet
    response = client.get(
        url,
        HTTP_HOST='testserver.com',
        HTTP_REFERER='http://testserver.com/foo/',
    )

    # then the referer is not exposed to the template
    assert response.context_data['next_url'] == '/'
    assert response.status_code == 200


@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_internal_ingress_url_used_on_first_step(
    mock_lookup_by_slug, client
):
    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )
    # when an internal ingress url is set
    response = client.get(
        reverse('contact-us-routing-form', kwargs={'step': 'location'}),
        HTTP_REFERER='http://testserver.com/foo/',
        HTTP_HOST='testserver.com'
    )

    # then the referer is exposed to the template
    assert response.context_data['prev_url'] == 'http://testserver.com/foo/'
    assert response.status_code == 200


@mock.patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_external_ingress_url_not_used_on_first_step(
    mock_lookup_by_slug, client
):
    mock_lookup_by_slug.return_value = create_response(
        status_code=200,
        json_body={}
    )
    # when an external ingress url is set
    response = client.get(
        reverse('contact-us-routing-form', kwargs={'step': 'location'}),
        HTTP_REFERER='http://external.com/foo/',
        HTTP_HOST='testserver.com'
    )

    # then the referer is not exposed to the template
    assert 'prev_url' not in response.context_data
    assert response.status_code == 200


@pytest.mark.parametrize('current_step,choice', (
    (constants.DOMESTIC, constants.TRADE_OFFICE),
    (constants.INTERNATIONAL, constants.INVESTING),
    (constants.INTERNATIONAL, constants.BUYING),
))
@mock.patch('contact.views.IngressURLMixin.clear_ingress_url')
def test_ingress_url_cleared_on_redirect_away(
    mock_clear_ingress_url, current_step, choice
):
    mock_clear_ingress_url.return_value = None

    form = ChoiceForm(data={'choice': choice})

    view = views.RoutingFormView()
    view.steps = mock.Mock(current=current_step)
    view.storage = mock.Mock()
    view.url_name = 'triage-wizard'

    assert form.is_valid()


@mock.patch('captcha.fields.ReCaptchaField.clean')
@mock.patch('directory_forms_api_client.actions.ZendeskAction')
def test_selling_online_overseas_contact_form_submission(
    mock_zendesk_action, mock_clean, captcha_stub, company_profile, client
):
    company_profile.return_value = None

    url_name = 'contact-us-soo'
    view_name = 'selling_online_overseas_form_view'

    response = client.post(
        reverse(url_name, kwargs={'step': 'organisation'}),
        {
            view_name + '-current_step': 'organisation',
            'organisation-soletrader': False,
            'organisation-company_name': 'Example corp',
            'organisation-company_number': 213123,
            'organisation-company_postcode': 'FOO BAR',
            'organisation-website_address': 'http://example.com'
        }
    )
    assert response.status_code == 302

    response = client.post(
        reverse(url_name, kwargs={'step': 'organisation-details'}),
        {
            view_name + '-current_step': 'organisation-details',
            'organisation-details-turnover': 'Under 100k',
            'organisation-details-sku_count': 12,
            'organisation-details-trademarked': True,
        }
    )
    assert response.status_code == 302

    response = client.post(
        reverse(url_name, kwargs={'step': 'your-experience'}),
        {
            view_name + '-current_step': 'your-experience',
            'your-experience-experience': 'Not yet',
            'your-experience-description': 'help!',
        }
    )
    assert response.status_code == 302

    response = client.post(
        reverse(url_name, kwargs={'step': 'contact-details'}),
        {
            view_name + '-current_step': 'contact-details',
            'contact-details-contact_name': 'Foo Example',
            'contact-details-contact_email': 'test@example.com',
            'contact-details-phone': '0324234243',
            'contact-details-email_pref': True,
            'contact-details-terms_agreed': True,
            'contact-details-captcha': captcha_stub,
        }
    )
    assert response.status_code == 302

    response = client.get(response.url)

    assert response.status_code == 302
    assert response.url == reverse(
        'contact-us-selling-online-overseas-success'
    )
    assert mock_clean.call_count == 1
    assert mock_zendesk_action.call_count == 1
    assert mock_zendesk_action.call_args == mock.call(
        subject=settings.CONTACT_SOO_ZENDESK_SUBJECT,
        full_name='Foo Example',
        email_address='test@example.com',
        service_name='Selling online overseas',
        form_url=reverse(
            'contact-us-soo', kwargs={'step': 'organisation'}
        )
    )
    assert mock_zendesk_action().save.call_count == 1
    assert mock_zendesk_action().save.call_args == mock.call({
        'ingress_url': None,
        'soletrader': False,
        'company_name': 'Example corp',
        'company_number': '213123',
        'company_postcode': 'FOO BAR',
        'website_address': 'http://example.com',
        'turnover': 'Under 100k',
        'sku_count': 12,
        'trademarked': True,
        'experience': 'Not yet',
        'description': 'help!',
        'contact_name': 'Foo Example',
        'contact_email': 'test@example.com',
        'phone': '0324234243',
        'email_pref': True,
    })


def test_selling_online_overseas_contact_form_initial_data(client):
    response_one = client.get(
        reverse('contact-us-soo', kwargs={'step': 'organisation'}),
    )
    assert response_one.context_data['form'].initial == {
        'soletrader': False,
        'company_name': 'Example corp',
        'company_number': 1234567,
        'company_postcode': 'Foo Bar',
        'website_address': 'http://www.example.com',
    }

    response_two = client.get(
        reverse('contact-us-soo', kwargs={'step': 'organisation-details'}),
    )
    assert response_two.context_data['form'].initial == {}

    response_three = client.get(
        reverse('contact-us-soo', kwargs={'step': 'your-experience'}),
    )
    assert response_three.context_data['form'].initial == {}

    response_four = client.get(
        reverse('contact-us-soo', kwargs={'step': 'contact-details'}),
    )
    assert response_four.context_data['form'].initial == {
        'contact_name': 'Foo Example',
        'contact_email': 'test@foo.com',
        'phone': '07171771717',
    }


def test_contact_soo_feature_flag_off(settings, client):
    settings.FEATURE_FLAGS['SOO_CONTACT_FORM_ON'] = False

    response = client.get(
        reverse('contact-us-soo', kwargs={'step': 'organisation'}),
    )

    assert response.status_code == 404


def test_office_finder_valid(office_details, client):
    url = api_client.exporting.endpoints['lookup-by-postcode'].format(
        postcode='ABC123'
    )

    with requests_mock.mock() as mock:
        mock.get(url, json=office_details)
        response = client.get(reverse('office-finder'), {'postcode': 'ABC123'})

    assert response.status_code == 200
    assert response.context_data['office_details'] == {
        'address': (
            'The International Trade Centre\n'
            '5 Merus Court\n'
            'Meridian Business Park\n'
            'Leicester\n'
            'LE19 1RJ'
        ),
        'region_id': 'east_midlands',
        'name': 'DIT East Midlands',
        'address_street': (
            'The International Trade Centre, '
            '5 Merus Court, '
            'Meridian Business Park'
        ),
        'address_city': 'Leicester',
        'address_postcode': 'LE19 1RJ',
        'email': 'test+east_midlands@examoke.com',
        'phone': '0345 052 4001',
        'phone_other': '',
        'phone_other_comment': '',
        'website': None
    }


@pytest.mark.parametrize('flag_value,expected_url', (
    (True, reverse('office-finder')),
    (False, views.LazyOfficeFinderURL()),
))
def test_lazy_office_finder_url_on(flag_value, expected_url, settings):
    settings.FEATURE_FLAGS['OFFICE_FINDER_ON'] = flag_value

    url = views.LazyOfficeFinderURL()

    assert url == expected_url


def test_office_finder_contact_feature_off(client, settings):
    settings.FEATURE_FLAGS['OFFICE_FINDER_ON'] = False

    url = reverse('office-finder-contact', kwargs={'postcode': 'FOOBAR'})

    response = client.get(url)

    assert response.status_code == 404


def test_contact_us_office_success_feature_off(client, settings):
    settings.FEATURE_FLAGS['OFFICE_FINDER_ON'] = False

    url = reverse('contact-us-office-success', kwargs={'postcode': 'FOOBAR'})

    response = client.get(url)

    assert response.status_code == 404
