from rest_framework import serializers
from movie.models import Movie, Rating
from omdb import OMDBClient
from django.conf import settings


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'


class TopMoviesSerializer(serializers.ModelSerializer):
    movie_id = serializers.IntegerField(source='id')
    total_comments = serializers.IntegerField()
    rank = serializers.IntegerField()

    class Meta:
        model = Movie
        fields = ['movie_id', 'total_comments', 'rank']


class MovieSerializer(serializers.ModelSerializer):
    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ['id', 'title', 'year', 'rated', 'released', 'runtime',
                  'genre', 'director', 'writer', 'actors', 'plot', 'language',
                  'country', 'awards', 'poster', 'metascore',
                  'imdb_rating', 'imdb_votes', 'imdb_id', 'type',
                  'dvd', 'box_office', 'production', 'website', 'ratings']

    def create(self, validated_data):
        """
        Overriden create method. This is caused by the fact, that when
        movie title is posted, we need to call external API to fill in
        movie info.
        There are a few checks: if movie even exists, if such movie is
        already in database and if returned info is even about the movie.
        :param validated_data: validated data used to create instances.
        :return: movie instance (got or created)
        """
        title = validated_data.get('title', None)

        try:
            movie = Movie.objects.get(title=title)
        except Movie.DoesNotExist:
            if title:
                client = OMDBClient(apikey=settings.API_KEY)
                fetched_data = client.get(title=title)

                if not fetched_data:
                    raise serializers.ValidationError('Invalid title.')

                if fetched_data['type'] != 'movie':
                    raise serializers.ValidationError('Only movies avaliable.')

                fetched_data.pop('response')
                ratings = fetched_data.pop('ratings')

                movie, created = Movie.objects.get_or_create(**fetched_data)

                for rating in ratings:
                    Rating.objects.create(**rating, movie=movie)
            else:
                raise serializers.ValidationError('Invalid request data!')
        return movie

