from captcha.fields import ReCaptchaField
from directory_constants.constants import choices, urls
from directory_components import forms, fields, widgets

from django.forms import Textarea, TextInput, ValidationError
from django.utils.html import mark_safe


class CategoryForm(forms.Form):
    error_css_class = 'input-field-container has-error'

    CATEGORY_CHOICES = (
        'Securing upfront funding',
        'Offering competitive but secure payment terms',
        'Guidance on export finance and insurance',
    )
    categories = fields.MultipleChoiceField(
        label='',
        widget=widgets.CheckboxSelectInlineLabelMultiple(
            attrs={'id': 'checkbox-multiple'},
            use_nice_ids=True,
        ),
        choices=((choice, choice) for choice in CATEGORY_CHOICES)
    )


class PersonalDetailsForm(forms.Form):
    error_css_class = 'input-field-container has-error'

    firstname = fields.CharField(label='Yout first name')
    lastname = fields.CharField(label='Your last name')
    position = fields.CharField(label='Position in company')
    email = fields.EmailField(label='Email address')
    phone = fields.CharField(label='Phone')


class CompanyDetailsForm(forms.Form):

    EXPORT_CHOICES = (
        'I have customers outside the UK',
        'I supply UK companies that sell overseas',
        'I don\'t currently export or supply businesses that export',
    )
    INDUSTRY_CHOICES = [
        (value.replace('_', ' ').title(), label)
        for (value, label) in choices.INDUSTRIES
    ] + [('Other', 'Other')]

    error_css_class = 'input-field-container has-error'

    trading_name = fields.CharField(label='Trading name')
    company_number = fields.CharField(
        label='Companies House number', required=False
    )
    not_companies_house = fields.BooleanField(
        label='Not registered with Companies House',
        required=False,
    )
    address_line_one = fields.CharField(label='Building and street')
    address_line_two = fields.CharField(label='', required=False)
    address_town_city = fields.CharField(label='Town or city')
    address_country = fields.CharField(label='Country')
    address_post_code = fields.CharField(label='Postcode')
    industry = fields.ChoiceField(
        initial='thing',
        choices=INDUSTRY_CHOICES
    )
    industry_other = fields.CharField(
        label='Type in your industry',
        widget=TextInput(attrs={'class': 'js-field-other'}),
        required=False,
    )

    export_status = fields.MultipleChoiceField(
        label='Do you currently export',
        help_text='Select all that apply',
        widget=widgets.CheckboxSelectInlineLabelMultiple(
            attrs={'id': 'checkbox-multiple'},
            use_nice_ids=True,
        ),
        choices=((choice, choice) for choice in EXPORT_CHOICES),
    )

    def clean(self):
        cleaned_data = super().clean()
        if (
            not cleaned_data.get('company_number')
            and not cleaned_data.get('not_companies_house')
        ):
            raise ValidationError(
                {'company_number': 'This field is required.'}
            )
        return cleaned_data


class HelpForm(forms.Form):
    error_css_class = 'input-field-container has-error'

    comment = fields.CharField(label='', widget=Textarea)
    terms_agreed = fields.BooleanField(
        label=mark_safe(
            'Tick this box to accept the '
            '<a href="{url}" target="_blank">terms and '
            'conditions</a> of the great.gov.uk service.'.format(
                url=urls.INFO_TERMS_AND_CONDITIONS)
        )
    )
    captcha = ReCaptchaField()
