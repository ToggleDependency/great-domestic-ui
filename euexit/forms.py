from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
from directory_constants import choices
from directory_constants.urls import domestic as domestic_urls
from directory_components import forms
from directory_forms_api_client.forms import ZendeskActionMixin
from directory_validators.url import not_contains_url_or_email
from directory_validators.string import no_html

from django.forms import Select, Textarea
from django.utils.html import mark_safe

from core.forms import ConsentFieldMixin


COMPANY = 'COMPANY'

COMPANY_CHOICES = (
    (COMPANY, 'Company'),
    ('OTHER', 'Other type of organisation'),
)


TERMS_LABEL = mark_safe(
    'Tick this box to accept the '
    f'<a href="{domestic_urls.TERMS_AND_CONDITIONS}" target="_blank">terms and '
    'conditions</a> of the great.gov.uk service.'
)


class FieldsMutationMixin:
    def __init__(self, field_attributes, *args, **kwargs):
        for field_name, field in self.base_fields.items():
            attributes = field_attributes.get(field_name)
            if attributes:
                field.__dict__.update(attributes)
        super().__init__(*args, **kwargs)


class SerializeMixin:
    def __init__(self, ingress_url, *args, **kwargs):
        self.ingress_url = ingress_url
        super().__init__(*args, **kwargs)

    @property
    def serialized_data(self):
        data = self.cleaned_data.copy()
        data['ingress_url'] = self.ingress_url
        del data['captcha']
        return data

    @property
    def full_name(self):
        assert self.is_valid()
        data = self.cleaned_data
        return f'{data["first_name"]} {data["last_name"]}'


class InternationalContactForm(
    FieldsMutationMixin, SerializeMixin, ZendeskActionMixin, forms.Form
):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    organisation_type = forms.ChoiceField(
        label_suffix='',
        widget=forms.RadioSelect(),
        choices=COMPANY_CHOICES,
    )
    company_name = forms.CharField()
    country = forms.ChoiceField(
        choices=[('', 'Please select')] + choices.COUNTRY_CHOICES,
        widget=Select(),
    )
    city = forms.CharField()
    comment = forms.CharField(
        widget=Textarea,
        validators=[no_html, not_contains_url_or_email]
    )
    captcha = ReCaptchaField(
        label='',
        label_suffix='',
        widget=ReCaptchaV3()
    )
    terms_agreed = forms.BooleanField(
        label=TERMS_LABEL
    )


class DomesticContactForm(FieldsMutationMixin, SerializeMixin, ZendeskActionMixin, ConsentFieldMixin, forms.Form):

    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    organisation_type = forms.ChoiceField(
        label_suffix='',
        widget=forms.RadioSelect(),
        choices=COMPANY_CHOICES
    )
    company_name = forms.CharField()
    comment = forms.CharField(
        widget=Textarea,
        validators=[no_html, not_contains_url_or_email]
    )
    captcha = ReCaptchaField(
        label='',
        label_suffix='',
        widget=ReCaptchaV3()
    )
