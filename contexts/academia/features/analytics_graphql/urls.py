from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView

from .schema import schema

app_name = "analytics_graphql"

urlpatterns = [
    path("", login_required(csrf_exempt(GraphQLView.as_view(schema=schema, graphql_ide="graphiql"))), name="endpoint"),
]
