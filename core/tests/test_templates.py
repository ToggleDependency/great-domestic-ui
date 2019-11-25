from unittest.mock import patch

from django.template.loader import render_to_string

from core.tests.helpers import create_response


def test_error_templates(rf):
    template_name = '404.html'
    assert render_to_string(template_name, {'request': rf.get('/')})


@patch('directory_cms_client.client.cms_api_client.lookup_by_path')
def test_404_custom_template(mock_cms_404, settings, client):
    mock_cms_404.return_value = create_response({}, status_code=404)
    settings.DEBUG = False
    response = client.get('/this-is-not-a-valid-url/')
    assert response.status_code == 404
    expected_text = bytes(
        'If you entered a web address please check'
        ' it’s correct.', 'utf8')
    assert expected_text in response.content
