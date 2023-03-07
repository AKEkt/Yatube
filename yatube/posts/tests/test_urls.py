from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.user)

    def test_url_guest_client(self):
        """Ответ страниц доступых любому пользователю.
        """
        url_names = {
            '/': HTTPStatus.OK,
            '/group/Тестовый слаг/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for address, http_code in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_code)

    def test_url_authorized_client(self):
        """Ответ страниц авторизованному пользователю-автору 200.
        """
        url_names = [
            '/create/',
            '/posts/1/edit/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_guest_client(self):
        """Проверка HTML-шаблонов для неавторизованного пользователя.
        """
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/Тестовый слаг/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_template_authorized_client(self):
        """Проверка HTML-шаблонов для авторизованного пользователя.
        """
        template = 'posts/create_post.html'
        url_names = [
            '/create/',
            '/posts/1/edit/'
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_redirect_anonymous_on_login_post_create(self):
        """Страница по адресу /create/ перенаправит user на login.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_redirect_anonymous_on_login_post_edit(self):
        """Страница по адресу /posts/1/edit/ перенаправит user на login.
        """
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/'
        )

    def test_redirect_anonymous_on_login_post_comment(self):
        """Страница по адресу /posts/1/comment/ перенаправит user на login.
        """
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/comment/'
        )
