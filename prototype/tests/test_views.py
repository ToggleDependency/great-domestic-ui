from unittest.mock import patch, PropertyMock
from bs4 import BeautifulSoup
from django.urls import reverse

from core.tests.helpers import create_response


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_prototype_landing_page_news_section(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['NEWS_SECTION_ON'] = True

    url = reverse('landing-page')

    page = {
        'news_title': 'News',
        'news_description': '<p>Lorem ipsum</p>',
        'articles': [
            {'article_title': 'News article 1'},
            {'article_title': 'News article 2'},
        ],
    }

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=page
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/landing_page.html']

    assert page['news_title'] in str(response.content)
    assert '<p class="body-text">Lorem ipsum</p>' in str(response.content)
    assert 'News article 1' in str(response.content)
    assert 'News article 2' in str(response.content)


test_topic_page = {
    'title': 'Markets CMS admin title',
    'landing_page_title': 'Markets',
    'hero_image': {'url': 'markets.jpg'},
    'child_pages': [
        {
            'landing_page_title': 'Africa market information',
            'full_path': '/markets/africa/',
            'hero_image': {'url': 'africa.png'},
            'hero_image_thumbnail': {'url': 'africa.jpg'},
            'articles_count': 0,
            'last_published_at': '2018-10-01T15:15:53.927833Z'
        },
        {
            'landing_page_title': 'Asia market information',
            'full_path': '/markets/asia/',
            'hero_image': {'url': 'asia.png'},
            'hero_image_thumbnail': {'url': 'asia.jpg'},
            'articles_count': 3,
            'last_published_at': '2018-10-01T15:16:30.583279Z'
        }
    ],
    "page_type": "TopicLandingPage",
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_advice_page_404_when_export_journey_on(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['EXPORT_JOURNEY_ON'] = True

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_topic_page
    )

    url = reverse('advice')
    response = client.get(url)

    assert response.status_code == 404


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_landing_page_when_export_journey_off(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['EXPORT_JOURNEY_ON'] = False

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body={
            'news_title': 'News',
            'news_description': '<p>Lorem ipsum</p>',
            'articles': [
                {'article_title': 'News article 1'},
                {'article_title': 'News article 2'},
            ],
        }
    )

    url = reverse('landing-page')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/landing_page.html']


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_landing_page_when_export_journey_on(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['EXPORT_JOURNEY_ON'] = True

    url = reverse('landing-page')
    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['core/landing-page.html']


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_advice_page_200_when_export_journey_off(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['EXPORT_JOURNEY_ON'] = False

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_topic_page
    )

    url = reverse('advice')
    response = client.get(url)

    assert response.status_code == 200


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_country_guide_article_404_when_prototype_feature_off(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = False

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_topic_page
    )

    url = reverse('country-guide-article', kwargs={
        'region': 'asia-pacific',
        'country': 'australia',
        'slug': 'exporting-to-australia'
    })

    response = client.get(url)

    assert response.status_code == 404


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_country_guide_article_404_when_prototype_feature_on(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_topic_page
    )

    url = reverse('country-guide-article', kwargs={
        'region': 'asia-pacific',
        'country': 'australia',
        'slug': 'exporting-to-australia'
    })

    response = client.get(url)

    assert response.status_code == 200


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_prototype_advice_page(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    url = reverse('advice', kwargs={'slug': 'advice'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_topic_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/topic_list.html']

    assert test_topic_page['title'] not in str(response.content)
    assert test_topic_page['landing_page_title'] in str(response.content)

    assert 'Asia market information' in str(response.content)
    assert 'Africa market information' not in str(response.content)
    assert 'markets.jpg' in str(response.content)
    assert 'asia.jpg' in str(response.content)
    assert 'africa.jpg' not in str(response.content)
    assert '01 October 2018' in str(response.content)


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_prototype_article_detail_page_no_related_content(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    test_article_page_no_related_content = {
        "title": "Test article admin title",
        "article_title": "Test article",
        "article_teaser": "Test teaser",
        "article_image": {"url": "foobar.png"},
        "article_body_text": "<p>Lorem ipsum</p>",
        "related_pages": [],
        "full_path": "/advice/manage-legal-and-ethical-compliance/foo/",
        "last_published_at": "2018-10-09T16:25:13.142357Z",
        "meta": {
            "slug": "foo",
        },
        "page_type": "ArticlePage",
    }

    url = reverse(
        'manage-legal-and-ethical-compliance-article',
        kwargs={'slug': 'foo'}
    )

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_article_page_no_related_content
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/article_detail.html']

    assert 'Related content' not in str(response.content)


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_prototype_article_detail_page_related_content(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    article_page = {
        "title": "Test article admin title",
        "article_title": "Test article",
        "article_teaser": "Test teaser",
        "article_image": {"url": "foobar.png"},
        "article_body_text": "<p>Lorem ipsum</p>",
        "related_pages": [
            {
                "article_title": "Related article 1",
                "article_teaser": "Related article 1 teaser",
                "article_image_thumbnail": {"url": "related_article_one.jpg"},
                "full_path": "/markets/test/test-one",
                "meta": {
                    "slug": "test-one",
                }
            },
            {
                "article_title": "Related article 2",
                "article_teaser": "Related article 2 teaser",
                "article_image_thumbnail": {"url": "related_article_two.jpg"},
                "full_path": "/markets/test/test-two",
                "meta": {
                    "slug": "test-two",
                }
            },
        ],
        "full_path": "/markets/foo/bar/",
        "last_published_at": "2018-10-09T16:25:13.142357Z",
        "meta": {
            "slug": "bar",
        },
        "page_type": "ArticlePage",
    }

    url = reverse(
        'manage-legal-and-ethical-compliance-article',
        kwargs={'slug': 'foo'}
    )

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=article_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/article_detail.html']

    assert 'Related content' in str(response.content)
    soup = BeautifulSoup(response.content, 'html.parser')

    assert soup.find(
        id='related-article-test-one-link'
    ).attrs['href'] == '/markets/test/test-one'
    assert soup.find(
        id='related-article-test-two-link'
    ).attrs['href'] == '/markets/test/test-two'

    assert soup.find(
        id='related-article-test-one'
    ).select('h3')[0].text == 'Related article 1'
    assert soup.find(
        id='related-article-test-two'
    ).select('h3')[0].text == 'Related article 2'


test_news_list_page = {
    'title': 'News CMS admin title',
    'landing_page_title': 'News',
    'articles_count': 2,
    'articles': [
        {
            'article_title': 'Lorem ipsum',
            'full_path': '/eu-exit-news/lorem-ipsum/',
            'last_published_at': '2018-10-01T15:15:53.927833Z',
            'meta': {'slug': 'test-slug-one'},
        },
        {
            'article_title': 'Dolor sit amet',
            'full_path': '/eu-exit-news/dolor-sit-amet/',
            'last_published_at': '2018-10-01T15:16:30.583279Z',
            'meta': {'slug': 'test-slug-two'},
        }
    ],
    "page_type": "ArticleListingPage",
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_news_list_page_feature_flag_on(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['NEWS_SECTION_ON'] = True

    url = reverse('eu-exit-news-list')

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_news_list_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/domestic_news_list.html']

    assert test_news_list_page['title'] not in str(response.content)
    assert test_news_list_page['landing_page_title'] in str(response.content)
    assert 'Lorem ipsum' in str(response.content)
    assert 'Dolor sit amet' in str(response.content)


@patch('prototype.views.InternationalNewsListPageView.cms_component',
       new_callable=PropertyMock)
@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_international_news_list_page(
    mock_get_page, mock_get_component, client, settings
):
    settings.FEATURE_FLAGS['NEWS_SECTION_ON'] = True

    url = reverse('international-eu-exit-news-list')

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_news_list_page
    )
    mock_get_component.return_value = {
        'banner_label': 'EU exit updates',
        'banner_content': '<p>Lorem ipsum.</p>',
        'meta': {'languages': [['en-gb', 'English']]},
    }

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/international_news_list.html']

    assert test_news_list_page['title'] not in str(response.content)
    assert test_news_list_page['landing_page_title'] in str(response.content)
    assert 'Lorem ipsum' in str(response.content)
    assert 'Dolor sit amet' in str(response.content)


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_domestic_news_article_detail_page(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['NEWS_SECTION_ON'] = True

    test_article_page = {
        "title": "Test article admin title",
        "article_title": "Test news title",
        "article_teaser": "Test news teaser",
        "article_image": {"url": "foobar.png"},
        "article_body_text": "<p>Lorem ipsum</p>",
        "related_article_one_url": "",
        "related_article_one_title": "",
        "related_article_one_teaser": "",
        "related_article_two_url": "",
        "related_article_two_title": "",
        "related_article_two_teaser": "",
        "related_article_three_url": "",
        "related_article_three_title": "",
        "related_article_three_teaser": "",
        "full_path": "/markets/foo/bar/",
        "last_published_at": "2018-10-09T16:25:13.142357Z",
        "meta": {
            "slug": "foo",
        },
        "tags": [
            {"name": "Test tag", "slug": "test-tag-slug"}
        ],
        "page_type": "ArticlePage",
    }

    url = reverse('eu-exit-news-detail', kwargs={'slug': 'foo'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_article_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [
        'prototype/domestic_news_detail.html']

    assert 'Test news title' in str(response.content)
    assert 'Test news teaser' in str(response.content)
    assert 'Test tag' not in str(response.content)
    assert '<p class="body-text">Lorem ipsum</p>' in str(response.content)


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_international_news_article_detail_page(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['NEWS_SECTION_ON'] = True

    test_article_page = {
        "title": "Test article admin title",
        "article_title": "Test news title",
        "article_teaser": "Test news teaser",
        "article_image": {"url": "foobar.png"},
        "article_body_text": "<p>Lorem ipsum</p>",
        "related_article_one_url": "",
        "related_article_one_title": "",
        "related_article_one_teaser": "",
        "related_article_two_url": "",
        "related_article_two_title": "",
        "related_article_two_teaser": "",
        "related_article_three_url": "",
        "related_article_three_title": "",
        "related_article_three_teaser": "",
        "full_path": "/markets/foo/bar/",
        "last_published_at": "2018-10-09T16:25:13.142357Z",
        "meta": {
            "slug": "foo",
        },
        "page_type": "ArticlePage",
    }

    url = reverse('international-eu-exit-news-detail', kwargs={'slug': 'foo'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_article_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == [
        'prototype/international_news_detail.html']

    assert 'Test news title' in str(response.content)
    assert 'Test news teaser' not in str(response.content)
    assert '<p class="body-text">Lorem ipsum</p>' in str(response.content)


def test_news_list_page_feature_flag_off(client, settings):
    settings.FEATURE_FLAGS['NEWS_SECTION_ON'] = False

    url = reverse('eu-exit-news-list')

    response = client.get(url)

    assert response.status_code == 404


test_articles = [
    {
        'seo_title': 'SEO title article 1',
        'search_description': 'Search description article 1',
        'article_title': 'Article 1 title',
        'article_teaser': 'Article 1 teaser.',
        'article_image': {'url': 'article_image1.png'},
        'article_body_text': '<p>Lorem ipsum 1</p>',
        'last_published_at': '2018-10-01T15:16:30.583279Z',
        'full_path': '/topic/list/article-one/',
        'tags': [
            {'name': 'New to exporting', 'slug': 'new-to-exporting'},
            {'name': 'Export tips', 'slug': 'export-tips'}
        ],
        'meta': {'slug': 'article-one'}
    },
    {
        'seo_title': 'SEO title article 2',
        'search_description': 'Search description article 2',
        'article_title': 'Article 2 title',
        'article_teaser': 'Article 2 teaser.',
        'article_image': {'url': 'article_image2.png'},
        'article_body_text': '<p>Lorem ipsum 2</p>',
        'last_published_at': '2018-10-02T15:16:30.583279Z',
        'full_path': '/topic/list/article-two/',
        'tags': [
            {'name': 'New to exporting', 'slug': 'new-to-exporting'},
        ],
        'meta': {'slug': 'article-two'}
    },
]

test_list_page = {
    'title': 'List CMS admin title',
    'seo_title': 'SEO title article list',
    'search_description': 'Article list search description',
    'landing_page_title': 'Article list landing page title',
    'hero_image': {'url': 'article_list.png'},
    'hero_teaser': 'Article list hero teaser',
    'list_teaser': '<p>Article list teaser</p>',
    'articles': test_articles,
    'page_type': 'ArticleListingPage',
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_prototype_article_list_page(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    url = reverse('create-an-export-plan')

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_list_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/article_list.html']

    assert test_list_page['title'] not in str(response.content)
    assert test_list_page['landing_page_title'] in str(response.content)

    assert '01 October' in str(response.content)
    assert '02 October' in str(response.content)


test_tag_page = {
    'name': 'New to exporting',
    'articles': test_articles,
}


@patch('directory_cms_client.client.cms_api_client.lookup_by_tag')
def test_prototype_tag_list_page(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    url = reverse('tag-list', kwargs={'slug': 'new-to-exporting'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=test_tag_page
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.template_name == ['prototype/tag_list.html']

    assert '01 October' in str(response.content)
    assert '02 October' in str(response.content)
    assert 'Article 1 title' in str(response.content)
    assert 'Article 2 title' in str(response.content)
    assert '2 articles with tag:' in str(response.content)
    assert 'New to exporting' in str(response.content)


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_landing_page_header_footer(
    mock_get_page, client, settings
):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True
    settings.FEATURE_FLAGS['EXPORT_JOURNEY_ON'] = False

    url = reverse('landing-page')

    page = {
        'news_title': 'News',
        'news_description': '<p>Lorem ipsum</p>',
        'articles': [],
    }

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body=page
    )
    response = client.get(url)

    assert response.status_code == 200

    assert '/static/js/home' in str(response.content)
    assert 'Create an export plan' in str(response.content)

    soup = BeautifulSoup(response.content, 'html.parser')

    assert soup.find(id="header-dit-logo")


@patch('directory_cms_client.client.cms_api_client.lookup_by_slug')
def test_breadcrumbs_mixin(mock_get_page, client, settings):
    settings.FEATURE_FLAGS['PROTOTYPE_PAGES_ON'] = True

    url = reverse('create-an-export-plan-article', kwargs={'slug': 'foo'})

    mock_get_page.return_value = create_response(
        status_code=200,
        json_body={
            'page_type': 'ArticlePage'
        }
    )
    response = client.get(url)

    breadcrumbs = response.context_data['breadcrumbs']
    assert breadcrumbs == [
        {
            'url': '/advice/',
            'label': 'Advice'
        },
        {
            'url': '/advice/create-an-export-plan/',
            'label': 'Create an export plan'
        },
        {
            'url': '/advice/create-an-export-plan/foo/',
            'label': 'Foo'
        },
    ]
