from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
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

    def test_models_have_correct_group(self):
        """У модели Group корректно работает __str__."""
        group = PostModelTest.group
        self.assertEqual(str(group), 'Тестовая группа')

    def test_models_have_correct_post(self):
        """У модели Post корректно работает __str__."""
        post = PostModelTest.post
        self.assertEqual(str(post), 'Тестовый пост')
