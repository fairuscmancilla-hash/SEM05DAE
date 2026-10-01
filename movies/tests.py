"""Tests for the admin configuration and the public recommendation view."""

from django.contrib.admin.sites import site
from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse

from .management.commands.seed_movies import Command as SeedCommand
from .models import Genre, Movie, Person, Rating


class AdminConfigurationTests(TestCase):
    def test_all_models_are_registered(self):
        for model in (Movie, Genre, Person, Rating):
            self.assertIn(model, site._registry)

    def test_movie_admin_options(self):
        options = site._registry[Movie]
        self.assertEqual(
            list(options.list_display),
            ["title", "year", "genre_list", "average_score", "score_count"],
        )
        self.assertEqual(list(options.list_filter), ["genres", "year"])
        self.assertIn("title", options.search_fields)
        self.assertIn("created_at", options.readonly_fields)
        self.assertIn("updated_at", options.readonly_fields)

    def test_ratings_are_editable_from_the_movie_page(self):
        options = site._registry[Movie]
        self.assertTrue(options.inlines)
        self.assertIs(options.inlines[0].model, Rating)

    def test_audit_fields_cannot_be_written(self):
        movie = Movie.objects.create(title="Alien", year=1979)
        self.assertIsNotNone(movie.created_at)
        self.assertIsNotNone(movie.updated_at)


class RecommendationTests(TestCase):
    def setUp(self):
        self.scifi = Genre.objects.create(name="Science Fiction")
        self.drama = Genre.objects.create(name="Drama")
        self.matrix = Movie.objects.create(title="The Matrix", year=1999)
        self.matrix.genres.add(self.scifi)
        self.alien = Movie.objects.create(title="Alien", year=1979)
        self.alien.genres.add(self.scifi)
        self.godfather = Movie.objects.create(title="The Godfather", year=1972)
        self.godfather.genres.add(self.drama)
        Rating.objects.create(movie=self.matrix, score=10)
        Rating.objects.create(movie=self.alien, score=7)
        Rating.objects.create(movie=self.godfather, score=9)

    def test_recommendations_share_a_genre_and_exclude_the_movie(self):
        recommendations = self.matrix.recommended_movies()
        self.assertEqual([movie.pk for movie in recommendations], [self.alien.pk])

    def test_recommendations_are_ordered_by_avg_score(self):
        better = Movie.objects.create(title="Arrival", year=2016)
        better.genres.add(self.scifi)
        Rating.objects.create(movie=better, score=9)
        titles = [movie.title for movie in self.matrix.recommended_movies()]
        self.assertEqual(titles, ["Arrival", "Alien"])

    def test_avg_score(self):
        movie = Movie.objects.with_scores().get(pk=self.matrix.pk)
        self.assertEqual(movie.avg_score, 10)
        self.assertEqual(movie.rating_count, 1)

    def test_score_columns_survive_the_genres_join(self):
        movie = Movie.objects.filter(genres__pk=self.scifi.pk).with_scores().get(
            pk=self.matrix.pk
        )
        self.assertEqual(movie.avg_score, 10)
        self.assertEqual(movie.rating_count, 1)

    def test_movie_list_view(self):
        response = self.client.get(reverse("movies:movie_list"))
        self.assertEqual(response.status_code, 200)
        titles = [movie.title for movie in response.context["movies"]]
        self.assertEqual(titles, ["The Matrix", "The Godfather", "Alien"])

    def test_movie_detail_view_shows_recommendations(self):
        response = self.client.get(
            reverse("movies:movie_detail", args=[self.matrix.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [movie.title for movie in response.context["recommendations"]], ["Alien"]
        )

    def test_genre_detail_view(self):
        response = self.client.get(reverse("movies:genre_detail", args=[self.scifi.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["movies"]), 2)
        self.assertEqual(response.context["genre"], self.scifi)


class RolePermissionTests(TestCase):
    def test_seed_creates_the_editors_group_with_the_expected_permissions(self):
        SeedCommand().handle()
        group = Group.objects.get(name="editores")
        codenames = set(group.permissions.values_list("codename", flat=True))
        self.assertEqual(
            codenames,
            {
                "add_movie",
                "change_movie",
                "view_movie",
                "add_rating",
                "change_rating",
                "view_rating",
                "view_genre",
                "view_person",
            },
        )

    def test_editors_cannot_delete_movies(self):
        SeedCommand().handle()
        group = Group.objects.get(name="editores")
        self.assertFalse(
            group.permissions.filter(codename="delete_movie").exists()
        )

    def test_editor_cannot_reach_the_delete_view(self):
        SeedCommand().handle()
        editor = User.objects.get(username="editor")
        self.client.force_login(editor)
        movie = Movie.objects.first()
        delete_url = reverse("admin:movies_movie_delete", args=[movie.pk])
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Movie.objects.filter(pk=movie.pk).exists())

    def test_superuser_can_reach_the_delete_view(self):
        SeedCommand().handle()
        admin_user = User.objects.create_superuser(
            username="root", email="root@example.com", password="root12345"
        )
        self.client.force_login(admin_user)
        movie = Movie.objects.first()
        delete_url = reverse("admin:movies_movie_delete", args=[movie.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 200)

    def test_seed_data_meets_the_lab_requirements(self):
        SeedCommand().handle()
        self.assertEqual(Genre.objects.count(), 4)
        self.assertEqual(Movie.objects.count(), 10)
        self.assertGreaterEqual(
            Movie.objects.filter(ratings__isnull=False).distinct().count(), 5
        )

    def test_seed_command_is_idempotent(self):
        SeedCommand().handle()
        SeedCommand().handle()
        self.assertEqual(Movie.objects.count(), 10)

    def test_seed_flush_removes_the_catalogue(self):
        SeedCommand().handle()
        SeedCommand().handle(flush=True)
        self.assertEqual(Movie.objects.count(), 10)
        self.assertEqual(Rating.objects.count(), 14)

    def test_editor_permissions_do_not_grant_model_admin(self):
        editor = User.objects.get_or_create(username="editor")[0]
        editor.user_permissions.add(
            Permission.objects.get(codename="add_movie"),
        )
        self.assertFalse(editor.has_perm("movies.delete_movie"))
