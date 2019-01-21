from directory_constants.constants import cms, urls
from directory_cms_client.client import cms_api_client

from django.conf import settings
from django.contrib import sitemaps
from django.urls import reverse, RegexURLResolver
from django.utils.cache import set_response_etag
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.utils.functional import cached_property

from casestudy import casestudies
from core import helpers, mixins
from euexit.mixins import (
    HideLanguageSelectorMixin, EUExitFormsFeatureFlagMixin)


class SetEtagMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.method == 'GET':
            response.add_post_render_callback(set_response_etag)
        return response


class LandingPageView(TemplateView):
    template_name = 'article/landing_page.html'

    @cached_property
    def page(self):
        response = cms_api_client.lookup_by_slug(
            slug=cms.EXPORT_READINESS_HOME_SLUG,
            draft_token=self.request.GET.get('draft_token'),
        )
        return helpers.handle_cms_response_allow_404(response)

    def get(self, request, *args, **kwargs):
        redirector = helpers.GeoLocationRedirector(self.request)
        if redirector.should_redirect:
            return redirector.get_response()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            LANDING_PAGE_VIDEO_URL=settings.LANDING_PAGE_VIDEO_URL,
            page=self.page,
            casestudies=[
                casestudies.MARKETPLACE,
                casestudies.HELLO_BABY,
                casestudies.YORK,
            ],
            *args, **kwargs
        )


class CampaignPageView(
    mixins.CampaignPagesFeatureFlagMixin,
    mixins.GetCMSPageMixin,
    TemplateView
):
    template_name = 'core/campaign.html'

    @property
    def slug(self):
        return self.kwargs['slug']


class InternationalLandingPageView(
    mixins.TranslationsMixin,
    mixins.GetCMSPageMixin,
    mixins.GetCMSComponentMixin,
    TemplateView,
):
    template_name = 'core/landing_page_international.html'
    component_slug = cms.COMPONENTS_BANNER_INTERNATIONAL_SLUG
    slug = cms.EXPORT_READINESS_HOME_INTERNATIONAL_SLUG


class InternationalContactPageView(
    EUExitFormsFeatureFlagMixin,
    HideLanguageSelectorMixin,
    TemplateView,
):
    template_name = 'core/contact_page_international.html'

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            invest_contact_us_url=urls.build_invest_url('contact/'),
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
                'https://opportunities.export.great.gov.uk/opportunities/'
            ),
            slug=kwargs.get('slug', '')
        )

        query_string = self.request.META.get('QUERY_STRING')
        if query_string:
            redirect_url = "{redirect_url}?{query_string}".format(
                redirect_url=redirect_url, query_string=query_string
            )

        return redirect_url


class InterstitialPageExoppsView(SetEtagMixin, TemplateView):
    template_name = 'core/interstitial_exopps.html'

    def get_context_data(self, **kwargs):
        context = {
            'exopps_url': settings.SERVICES_EXOPPS_ACTUAL
            }
        return context


class StaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'daily'

    def items(self):
        # import here to avoid circular import
        from conf import urls
        from conf.url_redirects import redirects

        excluded_pages = [
            'triage-wizard'
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
        ]

        excluded_pages += dynamic_cms_page_url_names
        excluded_pages += [url.name for url in urls.article_urls]
        excluded_pages += [url.name for url in urls.news_urls]

        return [
            item.name for item in urls.urlpatterns
            if not isinstance(item, RegexURLResolver) and
            item not in redirects and
            item.name not in excluded_pages
        ]

    def location(self, item):
        if item == 'uk-export-finance-lead-generation-form':
            return reverse(item, kwargs={'step': 'contact'})
        return reverse(item)


class AboutView(SetEtagMixin, TemplateView):
    template_name = 'core/about.html'


class PrivacyCookiesDomesticCMS(mixins.GetCMSPageMixin, TemplateView):
    template_name = 'core/info_page.html'
    slug = cms.EXPORT_READINESS_PRIVACY_AND_COOKIES_SLUG


class PrivacyCookiesDomesticSubpageCMS(mixins.GetCMSPageMixin, TemplateView):
    template_name = 'core/privacy_subpage.html'

    @property
    def slug(self):
        return self.kwargs['slug']


class PrivacyCookiesInternationalCMS(PrivacyCookiesDomesticCMS):
    template_name = 'core/info_page_international.html'


class TermsConditionsDomesticCMS(mixins.GetCMSPageMixin, TemplateView):
    template_name = 'core/info_page.html'
    slug = cms.EXPORT_READINESS_TERMS_AND_CONDITIONS_SLUG


class TermsConditionsInternationalCMS(TermsConditionsDomesticCMS):
    template_name = 'core/info_page_international.html'


class PerformanceDashboardView(
    mixins.PerformanceDashboardFeatureFlagMixin,
    mixins.GetCMSPageMixin,
    TemplateView
):
    template_name = 'core/performance_dashboard.html'


class PerformanceDashboardGreatView(PerformanceDashboardView):
    slug = cms.EXPORT_READINESS_PERFORMANCE_DASHBOARD_SLUG


class PerformanceDashboardExportOpportunitiesView(PerformanceDashboardView):
    slug = cms.EXPORT_READINESS_PERFORMANCE_DASHBOARD_EXOPPS_SLUG


class PerformanceDashboardSellingOnlineOverseasView(PerformanceDashboardView):
    slug = cms.EXPORT_READINESS_PERFORMANCE_DASHBOARD_SOO_SLUG


class PerformanceDashboardTradeProfilesView(PerformanceDashboardView):
    slug = cms.EXPORT_READINESS_PERFORMANCE_DASHBOARD_TRADE_PROFILE_SLUG


class PerformanceDashboardInvestView(PerformanceDashboardView):
    slug = cms.EXPORT_READINESS_PERFORMANCE_DASHBOARD_INVEST_SLUG


class PerformanceDashboardNotesView(PerformanceDashboardView):
    slug = cms.EXPORT_READINESS_PERFORMANCE_DASHBOARD_NOTES_SLUG
    template_name = 'core/performance_dashboard_notes.html'


class ServiceNoLongerAvailableView(TemplateView):
    template_name = 'core/service_no_longer_available.html'
