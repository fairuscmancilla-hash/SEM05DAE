from django.urls import path

from .views import GenreRecommendationView, MovieDetailView, MovieListView

app_name = "movies"

urlpatterns = [
    path("", MovieListView.as_view(), name="movie_list"),
    path("movies/<int:pk>/", MovieDetailView.as_view(), name="movie_detail"),
    path("genres/<int:pk>/", GenreRecommendationView.as_view(), name="genre_detail"),
]
