import logging

from directory_constants import slugs
from directory_cms_client.client import cms_api_client
from directory_ch_client import ch_search_api_client
from directory_forms_api_client.helpers import FormSessionMixin, Sender

from django.contrib import sitemaps
from django.http import JsonResponse
from django.urls import reverse
from django.utils.cache import set_response_etag
from django.views.generic import FormView, TemplateView
from django.views.generic.base import RedirectView, View
from django.utils.functional import cached_property

from core import helpers, mixins, forms
from content.views import CMSPageView

logger = logging.getLogger(__name__)


class SetEtagMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.method == 'GET':
            response.add_post_render_callback(set_response_etag)
        return response


class LandingPageView(TemplateView):

    template_name = 'core/landing_page.html'

    @cached_property
    def sector_list(self):
        return helpers.handle_cms_response(cms_api_client.list_industry_tags())

    @cached_property
    def page(self):
        response = cms_api_client.lookup_by_slug(
            slug=slugs.GREAT_HOME,
            draft_token=self.request.GET.get('draft_token'),
        )
        return helpers.handle_cms_response(response)

    def get(self, request, *args, **kwargs):
        redirector = helpers.GeoLocationRedirector(self.request)
        if redirector.should_redirect:
            return redirector.get_response()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        sorted_sectors = sorted(self.sector_list, key=lambda x: x['pages_count'], reverse=True)
        top_sectors = sorted_sectors[:6]
        return super().get_context_data(
            page=self.page,
            sector_list=top_sectors,
            sector_form=forms.SectorPotentialForm(sector_list=self.sector_list),
            *args, **kwargs
        )


class QuerystringRedirectView(RedirectView):
    query_string = True


class TranslationRedirectView(RedirectView):
    language = None
    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        """
        Return the URL redirect
        """
        url = super().get_redirect_url(*args, **kwargs)

        if self.language:
            # Append 'lang' to query params
            if self.request.META.get('QUERY_STRING'):
                concatenation_character = '&'
            # Add 'lang' query param
            else:
                concatenation_character = '?'

            url = '{}{}lang={}'.format(
                url, concatenation_character, self.language
            )

        return url


class OpportunitiesRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        redirect_url = '{export_opportunities_url}{slug}/'.format(
            export_opportunities_url=(
                '/export-opportunities/'
            ),
            slug=kwargs.get('slug', '')
        )

        query_string = self.request.META.get('QUERY_STRING')
        if query_string:
            redirect_url = "{redirect_url}?{query_string}".format(
                redirect_url=redirect_url, query_string=query_string
            )

        return redirect_url


class StaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'daily'

    def items(self):
        # import here to avoid circular import
        from conf import urls
        from conf.url_redirects import redirects

        excluded_pages = [
            'triage-wizard',
            'international-trade',
            'international-trade-home',
            'international-investment-support-directory-home',
            'international-investment-support-directory',
        ]
        dynamic_cms_page_url_names = [
            'privacy-and-cookies-subpage',
            'contact-us-export-opportunities-guidance',
            'contact-us-great-account-guidance',
            'contact-us-export-advice',
            'contact-us-soo',
            'campaign-page',
            'contact-us-routing-form',
            'office-finder-contact',
            'contact-us-office-success',
            'report-ma-barrier',
            'contact-us-exporting-guidance',
            'contact-us-exporting-to-the-uk-guidance',
            'tree-based-url',
        ]

        excluded_pages += dynamic_cms_page_url_names
        excluded_pages += [url.name for url in urls.article_urls]

        return [
            item.name for item in urls.urlpatterns
            if item not in redirects and
            item.name not in excluded_pages
        ]

    def location(self, item):
        if item == 'uk-export-finance-lead-generation-form':
            return reverse(item, kwargs={'step': 'contact'})
        elif item == 'report-ma-barrier':
            return reverse(item, kwargs={'step': 'about'})
        return reverse(item)


class PrivacyCookiesDomesticCMS(CMSPageView):
    template_name = 'core/info_page.html'
    slug = slugs.GREAT_PRIVACY_AND_COOKIES


class TermsConditionsDomesticCMS(CMSPageView):
    template_name = 'core/info_page.html'
    slug = slugs.GREAT_TERMS_AND_CONDITIONS


class AccessibilityStatementDomesticCMS(CMSPageView):
    template_name = 'core/info_page.html'
    slug = slugs.GREAT_ACCESSIBILITY_STATEMENT


class CookiePreferencesPageView(TemplateView):
    template_name = 'core/cookie-preferences.html'


class ServiceNoLongerAvailableView(mixins.GetCMSPageMixin, TemplateView):
    slug = 'advice'
    template_name = 'core/service_no_longer_available.html'


class CompaniesHouseSearchApiView(View):
    form_class = forms.CompaniesHouseSearchForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(data=request.GET)
        if not form.is_valid():
            return JsonResponse(form.errors, status=400)

        api_response = ch_search_api_client.company.search_companies(query=form.cleaned_data['term'])
        api_response.raise_for_status()
        return JsonResponse(api_response.json()['items'], safe=False)


class SendNotifyMessagesMixin:

    def send_agent_message(self, form):
        sender = Sender(
            email_address=form.cleaned_data['email'],
            country_code=None,
        )
        response = form.save(
            template_id=self.notify_settings.agent_template,
            email_address=self.notify_settings.agent_email,
            form_url=self.request.get_full_path(),
            form_session=self.form_session,
            sender=sender,
        )
        response.raise_for_status()

    def send_user_message(self, form):
        # no need to set `sender` as this is just a confirmation email.
        response = form.save(
            template_id=self.notify_settings.user_template,
            email_address=form.cleaned_data['email'],
            form_url=self.request.get_full_path(),
            form_session=self.form_session,
        )
        response.raise_for_status()

    def form_valid(self, form):
        self.send_agent_message(form)
        self.send_user_message(form)
        return super().form_valid(form)


class BaseNotifyFormView(
    FormSessionMixin, SendNotifyMessagesMixin, FormView
):
    page_type = 'ContactPage'


class ServicesView(TemplateView):
    template_name = 'core/services.html'
    page_type = 'ServicesLandingPage'


class OrphanCMSArticlePageView(CMSPageView):

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            hide_breadcrumbs=True,
            *args, **kwargs)
