import logging
from requests.exceptions import RequestException

from django.urls import reverse
from django.views.generic import TemplateView

from activitystream import helpers

logger = logging.getLogger(__name__)


class SearchView(TemplateView):
    """ Search results page.

        URL parameters: 'q'    String to be searched
                        'page' Int results page number
    """
    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        query = self.request.GET.get('q', '')
        page = helpers.sanitise_page(self.request.GET.get('page', '1'))
        elasticsearch_query = helpers.format_query(query, page)

        try:
            response = helpers.search_with_activitystream(elasticsearch_query)
        except RequestException:
            logger.error(
                "Activity Stream connection for"
                "Search failed. Query: '{}'".format(query))
            return {
                'error_status_code': 500,
                'error_message': "Activity Stream connection failed",
                'query': query
            }
        else:
            if response.status_code != 200:
                return {
                    'error_message': response.content,
                    'error_status_code': response.status_code,
                    'query': query
                }
            else:
                return helpers.parse_results(response, query, page)


class SearchKeyPagesView(TemplateView):
    """ Returns data on key pages (such as the Get Finance homepage) to
        include in search that are otherwise not provided via other APIs.
    """
    template_name = 'search-key-pages.json'


def SearchFeedbackFormView(FormView):

    template_name = 'search_feedback.html'
    form_class = forms.CompanyHomeSearchForm
    success_url = reverse('search-feedback-received')

    def form_valid():
        form.save(
            email_address=form.cleaned_data['email'],
        )
        

        form = FeedbackForm(request.POST)
        if form.is_valid():


            # process the data in form.cleaned_data as required
            # ...
            return HttpResponseRedirect('/search/seach_feedback_thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NameForm()

    return render(request, '', {'form': form})


