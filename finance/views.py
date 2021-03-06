from directory_constants import slugs
from directory_forms_api_client.actions import PardotAction
from directory_forms_api_client.helpers import Sender
from formtools.wizard.views import NamedUrlSessionWizardView
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from core import mixins
from finance import forms


class TradeFinanceView(mixins.GetCMSPageMixin, TemplateView):
    template_name = 'finance/trade_finance.html'
    slug = slugs.GREAT_GET_FINANCE


@method_decorator(never_cache, name='dispatch')
class GetFinanceLeadGenerationFormView(
    mixins.PrepopulateFormMixin,
    mixins.PreventCaptchaRevalidationMixin,
    NamedUrlSessionWizardView
):
    success_url = reverse_lazy(
        'uk-export-finance-lead-generation-form-success'
    )

    PERSONAL_DETAILS = 'your-details'
    COMPANY_DETAILS = 'company-details'
    HELP = 'help'

    form_list = (
        (PERSONAL_DETAILS, forms.PersonalDetailsForm),
        (COMPANY_DETAILS, forms.CompanyDetailsForm),
        (HELP, forms.HelpForm),
    )
    templates = {
        PERSONAL_DETAILS: 'finance/lead_generation_form/step-personal.html',
        COMPANY_DETAILS: 'finance/lead_generation_form/step-company.html',
        HELP: 'finance/lead_generation_form/step-help.html',
    }

    def get_form_kwargs(self, *args, **kwargs):
        # skipping `PrepopulateFormMixin.get_form_kwargs`
        return super(mixins.PrepopulateFormMixin, self).get_form_kwargs(
            *args, **kwargs
        )

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)
        if self.request.user.is_authenticated:
            if step == self.PERSONAL_DETAILS and self.request.user.company:
                initial.update({
                    'email': self.request.user.email,
                    'phone': self.request.user.company['mobile_number'],
                    'firstname': self.guess_given_name,
                    'lastname': self.guess_family_name,
                })
            elif step == self.COMPANY_DETAILS and self.request.user.company:
                company = self.request.user.company
                initial.update({
                    'not_companies_house': False,
                    'company_number': company['number'],
                    'trading_name': company['name'],
                    'address_line_one': company['address_line_1'],
                    'address_line_two': company['address_line_2'],
                    'address_town_city': company['locality'],
                    'address_post_code': company['postal_code'],
                    'industry': (
                        company['sectors'][0] if company['sectors'] else None
                    ),
                })
        return initial

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_list, **kwargs):
        form_data = self.serialize_form_list(form_list)
        sender = Sender(email_address=form_data['email'], country_code=None)
        action = PardotAction(
            pardot_url=settings.UKEF_FORM_SUBMIT_TRACKER_URL,
            form_url=reverse(
                'uk-export-finance-lead-generation-form',
                kwargs={'step': self.PERSONAL_DETAILS}
            ),
            sender=sender,
        )
        response = action.save(form_data)
        response.raise_for_status()
        return redirect(self.success_url)

    @staticmethod
    def serialize_form_list(form_list):
        data = {}
        for form in form_list:
            data.update(form.cleaned_data)
        return data


class GetFinanceLeadGenerationSuccessView(TemplateView):
    template_name = 'finance/lead_generation_form/success.html'
