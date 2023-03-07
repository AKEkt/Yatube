import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
NUM_POSTS_0 = 0
NUM_POSTS_5 = 5
NUM_POSTS_10 = 10
ADD_NEW_POST = ADD_NEW_COMM = ONE_POST = 1
uploaded = SimpleUploadedFile(
    name='small.jpg',
    content=(
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    ),
    content_type='image/jpg',
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.user_3 = User.objects.create_user(username='auth_3')
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Тестовый_пост_2',
            group=Group.objects.create(
                title='Тестовая_группа_2',
                slug='Тест_слаг_2',
                description='Тестовое_описание_2',
            )
        )
        cls.group = Group.objects.create(
            title='Тестовая_группа',
            slug='Тест_слаг',
            description='Тестовое_описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый_пост',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(ViewsTests.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(ViewsTests.user_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(ViewsTests.user_3)

    def test_templates_pages(self):
        """URL-адрес использует соответствующий HTML-шаблоны.
        """
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'Тест_слаг'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'auth'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def context_test_equal(self, response):
        first_object = response.context['page_obj'][NUM_POSTS_0]
        self.assertEqual(first_object.text, ViewsTests.post.text)
        self.assertEqual(first_object.author, ViewsTests.user)
        self.assertEqual(first_object.group, ViewsTests.group)
        self.assertIn(uploaded.name, first_object.image.name)

    def test_correct_context_index(self):
        """В страницу index передан пост с картинкой в context.
        """
        response = self.guest_client.get(reverse('posts:index'))
        self.context_test_equal(response)

    def test_correct_context_group_list(self):
        """В страницу group_list передан передан пост с картинкой в context.
        """
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'Тест_слаг'}
        ))
        self.context_test_equal(response)

    def test_correct_context_profile(self):
        """В страницу profile передан пост с картинкой в context.
        """
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}
        ))
        self.context_test_equal(response)

    def test_correct_context_post_detail(self):
        """В страницу post_detail передан пост с картинкой в context.
        """
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '2'})
        ))
        self.assertEqual(response.context['post'].text, ViewsTests.post.text)
        self.assertEqual(response.context['post'].author, ViewsTests.user)
        self.assertEqual(
            response.context['post'].group, ViewsTests.group
        )
        self.assertIn(uploaded.name, response.context['post'].image.name)

    def test_type_fields(self):
        """Типы полей формы в словаре context соответствуют ожиданиям
        """
        templates_pages_names = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
        ]
        for template in templates_pages_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                form_fields = {
                    'group': forms.fields.ChoiceField,
                    'text': forms.fields.CharField,
                }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_new_post_not_other_group(self):
        """Новый пост не попадает на страницу группы к которой не принадлежит.
        """
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'Тест_слаг_2'})
        )
        first_object = response.context['page_obj'][NUM_POSTS_0]
        self.assertNotEqual(first_object.text, ViewsTests.post.text)
        self.assertNotEqual(first_object.group, ViewsTests.group)

    def test_comment_authorized_client(self):
        """Авторизированный пользователь может комментировать посты.
        """
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client_2.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + ADD_NEW_COMM)
        self.assertTrue(
            Comment.objects.filter(
                text='Комментарий'
            ).exists()
        )

    def test_follow_profile(self):
        """Авторизованный user может подписываться на других пользователей.
        """
        self.assertFalse(
            Follow.objects.filter(
                user=ViewsTests.user_3,
                author=ViewsTests.user
            ).exists()
        )
        response = self.authorized_client_3.get(
            reverse('posts:profile_follow', kwargs={'username': 'auth'})
        )
        self.assertRedirects(response, reverse('posts:follow_index'))
        self.assertTrue(
            Follow.objects.filter(
                user=ViewsTests.user_3,
                author=ViewsTests.user
            ).exists()
        )

    def test_unfollow_profile(self):
        """Авторизованный user может удалять авторов из подписок.
        """
        # Пользователь "auth_3" подписан на автора "auth"
        Follow.objects.create(
            user=ViewsTests.user_3,
            author=ViewsTests.user
        )
        response = self.authorized_client_3.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'auth'})
        )
        self.assertRedirects(response, reverse('posts:follow_index'))
        self.assertFalse(
            Follow.objects.filter(
                user=ViewsTests.user_3,
                author=ViewsTests.user
            ).exists()
        )

    def test_follow_index_add_posts(self):
        """В ленте пользователя появляются посты авторов, на
        которых подписан пользователь.
        """
        ViewsTests.post_new = Post.objects.create(
            text='Новый_пост',
            author=ViewsTests.user
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][NUM_POSTS_0]
        self.assertEqual(first_object.author, ViewsTests.user)
        self.assertEqual(first_object.text, ViewsTests.post_new.text)

    def test_follow_index_no_posts(self):
        """В ленте пользователя нет постов авторов, на
        которых пользователь не подписан.
        """
        ViewsTests.post_new = Post.objects.create(
            text='Новый_пост',
            author=ViewsTests.user_3
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][NUM_POSTS_0]
        self.assertNotEqual(first_object.author, ViewsTests.user_3)
        self.assertNotEqual(first_object.text, ViewsTests.post_new.text)

    def test_cache(self):
        """Тестирование cache для страниц index.
        """
        response = self.guest_client.get(reverse('posts:index'))
        page_before_del_post = response.content
        ViewsTests.post.delete()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(page_before_del_post, response.content)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(page_before_del_post, response.content)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая_группа',
            slug='Тест_слаг',
            description='Тестовое_описание',
        )
        for i in range(15):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый_пост',
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()

    def test_paginator(self):
        """Тестирование паджинатора для страниц index, group_list, profile.
        """
        templates_pages_names = [
            (reverse('posts:index')),
            (reverse('posts:group_list', kwargs={'slug': 'Тест_слаг'})),
            (reverse('posts:profile', kwargs={'username': 'auth'})),
        ]
        for template in templates_pages_names:
            with self.subTest(template=template):
                response = self.guest_client.get(template)
                self.assertEqual(len(
                    response.context['page_obj']), NUM_POSTS_10
                )
                response = self.guest_client.get(template + '?page=2')
                self.assertEqual(len(
                    response.context['page_obj']), NUM_POSTS_5
                )
