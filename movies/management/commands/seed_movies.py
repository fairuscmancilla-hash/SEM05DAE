"""Loads the sample data required by the lab: 10 movies, 4 genres and ratings
on at least five of them."""

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie, Person, Rating

GENRES = ["Action", "Science Fiction", "Drama", "Animation"]

PEOPLE = {
    "Inception": ["Christopher Nolan", "Leonardo DiCaprio"],
    "Interstellar": ["Christopher Nolan", "Matthew McConaughey"],
    "The Godfather": ["Francis Ford Coppola", "Marlon Brando"],
    "Parasite": ["Bong Joon-ho", "Song Kang-ho"],
    "Spirited Away": ["Hayao Miyazaki", "Rumi Hiiragi"],
    "Toy Story": ["John Lasseter", "Tom Hanks"],
    "The Matrix": ["Lana Wachowski", "Lilly Wachowski", "Keanu Reeves"],
    "Whiplash": ["Damien Chazelle", "Miles Teller"],
    "Arrival": ["Denis Villeneuve", "Amy Adams"],
    "Alien": ["Ridley Scott", "Sigourney Weaver"],
}

MOVIES = [
    (
        "Inception",
        2010,
        ["Action", "Science Fiction"],
        "A thief who steals corporate secrets through dream-sharing technology.",
    ),
    (
        "The Matrix",
        1999,
        ["Science Fiction", "Action"],
        "A hacker discovers the world he lives in is a simulation.",
    ),
    (
        "Interstellar",
        2014,
        ["Science Fiction", "Drama"],
        "A team travels through a wormhole looking for a new home for humanity.",
    ),
    (
        "Arrival",
        2016,
        ["Science Fiction", "Drama"],
        "A linguist works with the military to talk with alien visitors.",
    ),
    (
        "Alien",
        1979,
        ["Science Fiction", "Action"],
        "The crew of a commercial spacecraft meets a deadly life form.",
    ),
    (
        "The Godfather",
        1972,
        ["Drama"],
        "An aging crime patriarch hands control of his dynasty to his son.",
    ),
    (
        "Parasite",
        2019,
        ["Drama"],
        "A poor family schemes to become employed by a wealthy household.",
    ),
    (
        "Whiplash",
        2014,
        ["Drama"],
        "A young jazz drummer is pushed by his instructor to reach perfection.",
    ),
    (
        "Spirited Away",
        2001,
        ["Animation", "Drama"],
        "A girl wanders into a world of spirits and must work to free her parents.",
    ),
    (
        "Toy Story",
        1995,
        ["Animation", "Action"],
        "Toys come to life when humans are not around.",
    ),
]

RATINGS = [
    ("Inception", "Ana", 10, "Perfect ending and a great soundtrack."),
    ("Inception", "Luis", 9, "Dense but worth every minute."),
    ("The Matrix", "Ana", 10, "A classic that still holds up."),
    ("The Matrix", "Rosa", 8, "Revolutionary, the last act drags a little."),
    ("Interstellar", "Luis", 9, "Ambitious and emotional."),
    ("Interstellar", "Rosa", 8, "Long, but the docking scene is superb."),
    ("The Godfather", "Ana", 9, "Still the benchmark for crime cinema."),
    ("Parasite", "Luis", 10, "A perfect script."),
    ("Parasite", "Rosa", 9, "The tonal shift is brilliant."),
    ("Spirited Away", "Ana", 9, "Beautiful animation and a great score."),
    ("Arrival", "Rosa", 8, "Quiet and thoughtful science fiction."),
    ("Alien", "Luis", 9, "Still terrifying."),
    ("Toy Story", "Ana", 8, "The first fully computer animated feature."),
    ("Whiplash", "Rosa", 8, "Relentless energy."),
]

EDITOR_PERMISSIONS = [
    "add_movie",
    "change_movie",
    "view_movie",
    "add_rating",
    "change_rating",
    "view_rating",
    "view_genre",
    "view_person",
]


class Command(BaseCommand):
    help = "Creates the sample catalogue, the 'editores' group and a demo user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete the existing catalogue before loading the sample data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("flush"):
            Rating.objects.all().delete()
            Movie.objects.all().delete()
            Person.objects.all().delete()
            Genre.objects.all().delete()
            self.stdout.write("Existing catalogue removed.")

        genres = {
            name: Genre.objects.get_or_create(name=name)[0] for name in GENRES
        }
        people = {}
        for full_name in {name for names in PEOPLE.values() for name in names}:
            first_name, _, last_name = full_name.partition(" ")
            people[full_name] = Person.objects.get_or_create(
                first_name=first_name, last_name=last_name
            )[0]

        movies = {}
        for title, year, genre_names, synopsis in MOVIES:
            movie, _ = Movie.objects.update_or_create(
                title=title, defaults={"year": year, "synopsis": synopsis}
            )
            movie.genres.set([genres[name] for name in genre_names])
            movie.people.set([people[name] for name in PEOPLE.get(title, [])])
            movies[title] = movie

        for title, reviewer, score, comment in RATINGS:
            Rating.objects.update_or_create(
                movie=movies[title],
                reviewer=reviewer,
                defaults={"score": score, "comment": comment},
            )

        group = self.create_editors_group()
        self.create_editor_user(group)

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {Genre.objects.count()} genres, {Movie.objects.count()} movies, "
                f"{Person.objects.count()} people and {Rating.objects.count()} ratings."
            )
        )
        self.stdout.write(
            "Group 'editores' ready. Demo user: editor / editor12345"
        )

    def create_editors_group(self):
        """Editors can add and change the catalogue but never delete it."""
        group, _ = Group.objects.get_or_create(name="editores")
        permissions = Permission.objects.filter(
            content_type__app_label="movies", codename__in=EDITOR_PERMISSIONS
        )
        group.permissions.set(permissions)
        return group

    def create_editor_user(self, group):
        user, created = User.objects.get_or_create(
            username="editor", defaults={"email": "editor@example.com"}
        )
        user.set_password("editor12345")
        user.is_staff = True
        user.save()
        user.groups.add(group)
        if created:
            self.stdout.write("Created user 'editor'.")
