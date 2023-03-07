from django.test import TestCase
from http import HTTPStatus


class CustomPagesErr(TestCase):
    def test_error_page(self):
        """Страница 404 отдаёт кастомный шаблон"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
