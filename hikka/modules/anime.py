from hikka.decorators import auth_required, permission_required
from hikka.services.permissions import PermissionService
from hikka.services.anime import AnimeService
from hikka.tools.parser import RequestParser
from flask import request, Blueprint
from hikka.tools import helpers
from hikka.errors import abort
from hikka import utils

blueprint = Blueprint("anime", __name__)

@blueprint.route("/anime/new", methods=["POST"])
@auth_required
@permission_required("global", "publishing")
def new_anime():
    result = {"error": None, "data": {}}

    parser = RequestParser()
    parser.argument("franchises", type=list, default=[], location="json")
    parser.argument("subtitles", type=list, default=[], location="json")
    parser.argument("voiceover", type=list, default=[], location="json")
    parser.argument("aliases", type=list, default=[], location="json")
    parser.argument("genres", type=list, default=[], location="json")
    parser.argument("category", type=helpers.category, required=True)
    parser.argument("description", type=helpers.string, required=True)
    parser.argument("state", type=helpers.state, required=True)
    parser.argument("team", type=helpers.team, required=True)
    parser.argument("season", type=int, choices=range(1, 5))
    parser.argument("title", type=dict, required=True)
    parser.argument("year", type=int, required=True)
    parser.argument("external", type=dict)
    parser.argument("total", type=int)
    args = parser.parse()

    title_parser = RequestParser()
    title_parser.argument("ua", type=helpers.string, location="title", required=True)
    title_parser.argument("jp", type=helpers.string, location="title")
    title_args = title_parser.parse(req=args)

    external_parser = RequestParser()
    external_parser.argument("myanimelist", type=int, location="external")
    external_parser.argument("toloka", type=int, location="external")
    external_args = external_parser.parse(req=args)

    title = AnimeService.get_title(title_args["ua"], title_args["jp"])
    slug = utils.create_slug(title_args["ua"])
    team = args["team"]

    helpers.is_member(request.account, [team])

    anime = AnimeService.create(
        title, args["description"],
        args["category"], args["state"],
        slug
    )

    for alias in args["aliases"]:
        if type(alias) is not str:
            return abort("general", "alias-invalid-type")

    anime.genres = []
    for slug in args["genres"]:
        genre = helpers.genre(slug)
        anime.genres.append(genre)

    anime.franchises = []
    for slug in args["franchises"]:
        franchise = helpers.franchise(slug)
        anime.franchises.append(franchise)

    fields = ["aliases", "year", "total"]
    for field in fields:
        anime[field] = args[field]

    fields = ["subtitles", "voiceover"]
    for field in fields:
        anime[field] = []
        for username in args[field]:
            account = helpers.account(username)
            anime[field].append(account)

    search = utils.create_search(anime.title.ua, anime.title.jp, anime.aliases)
    external = AnimeService.get_external(external_args["myanimelist"], external_args["toloka"])

    anime.external = external
    anime.search = search
    anime.teams = [team]

    if anime.external.myanimelist:
        anime.rating = utils.rating(anime.external.myanimelist)
        anime.save()

    result["data"] = anime.dict()
    anime.save()

    return result

@blueprint.route("/anime/edit", methods=["POST"])
@auth_required
@permission_required("global", "publishing")
def edit_anime():
    result = {"error": None, "data": {}}

    parser = RequestParser()
    parser.argument("params", type=dict, default={}, location="json")
    parser.argument("slug", type=helpers.anime, required=True)
    args = parser.parse()

    params_parser = RequestParser()
    params_parser.argument("season", type=int, choices=range(1, 5), location="params")
    params_parser.argument("description", type=helpers.string, location="params")
    params_parser.argument("category", type=helpers.category, location="params")
    params_parser.argument("state", type=helpers.state, location="params")
    params_parser.argument("franchises", type=list, location="params")
    params_parser.argument("subtitles", type=list, location="params")
    params_parser.argument("voiceover", type=list, location="params")
    params_parser.argument("external", type=dict, location="params")
    params_parser.argument("selected", type=bool, location="params")
    params_parser.argument("aliases", type=list, location="params")
    params_parser.argument("genres", type=list, location="params")
    params_parser.argument("title", type=dict, location="params")
    params_parser.argument("total", type=int, location="params")
    params_parser.argument("year", type=int, location="params")
    params_args = params_parser.parse(req=args)

    title_parser = RequestParser()
    title_parser.argument("jp", type=str, location="title")
    title_parser.argument("ua", type=str, location="title")
    title_args = title_parser.parse(req=params_args)

    external_parser = RequestParser()
    external_parser.argument("myanimelist", type=int, location="external")
    external_parser.argument("toloka", type=int, location="external")
    external_args = external_parser.parse(req=params_args)

    anime = args["slug"]
    helpers.is_member(request.account, anime.teams)

    if params_args["aliases"]:
        for alias in args["aliases"]:
            if type(alias) is not str:
                return abort("general", "alias-invalid-type")

    if params_args["genres"]:
        anime.genres = []
        for slug in params_args["genres"]:
            genre = helpers.genre(slug)
            anime.genres.append(genre)

    if params_args["franchises"]:
        anime.franchises = []
        for slug in params_args["franchises"]:
            franchise = helpers.franchise(slug)
            anime.franchises.append(franchise)

    fields = ["category", "description", "state", "year", "total", "selected", "aliases", "season"]
    for field in fields:
        if params_args[field]:
            anime[field] = params_args[field]

    fields = ["subtitles", "voiceover"]
    for field in fields:
        if params_args[field]:
            anime[field] = []
            for username in params_args[field]:
                account = helpers.account(username)
                anime[field].append(account)

    fields = ["jp", "ua"]
    for field in fields:
        if title_args[field]:
            anime.title[field] = title_args[field]

    if params_args["external"]:
        if external_args["myanimelist"]:
            anime.external.myanimelist = external_args["myanimelist"]
            anime.rating = utils.rating(anime.external.myanimelist)

        if external_args["toloka"]:
            anime.external.toloka = external_args["toloka"]

    if PermissionService.check(request.account, "global", "admin"):
        if params_args["selected"]:
            anime["selected"] = params_args["selected"]

    anime.search = utils.create_search(anime.title.ua, anime.title.jp, anime.aliases)
    anime.save()

    result["data"] = anime.dict()
    return result

@blueprint.route("/anime/list", methods=["POST"])
@auth_required
def list_anime():
    result = {"error": None, "data": []}

    parser = RequestParser()
    parser.argument("franchises", type=list, default=[], location="json")
    parser.argument("categories", type=list, default=[], location="json")
    parser.argument("ordering", type=list, default=[], location="json")
    parser.argument("states", type=list, default=[], location="json")
    parser.argument("genres", type=list, default=[], location="json")
    parser.argument("teams", type=list, default=[], location="json")
    parser.argument("query", type=str, default="")
    parser.argument("page", type=int, default=0)
    parser.argument("year", type=dict)
    args = parser.parse()

    year_parser = RequestParser()
    year_parser.argument("min", type=int, location="year")
    year_parser.argument("max", type=int, location="year")
    year_args = year_parser.parse(req=args)

    query = utils.search_query(args["query"])
    categories = []
    franchises = []
    ordering = []
    genres = []
    states = []
    teams = []

    for slug in args["categories"]:
        category = helpers.category(slug)
        categories.append(category)

    for slug in args["genres"]:
        genre = helpers.genre(slug)
        genres.append(genre)

    for slug in args["franchises"]:
        franchise = helpers.franchise(slug)
        franchises.append(franchise)

    for slug in args["states"]:
        state = helpers.state(slug)
        states.append(state)

    for slug in args["teams"]:
        team = helpers.team(slug)
        teams.append(team)

    for item in args["ordering"]:
        check = item
        if item[0] in ["+", "-"]:
            check = item[1:]

        if check in ("rating"):
            ordering.append(check)

    anime = AnimeService.search(
        query, year_args, categories,
        genres, franchises, states,
        teams, ordering, False,
        args["page"], account=request.account
    )

    for item in anime:
        result["data"].append(item.dict())

    return result

@blueprint.route("/anime/fetch/<string:slug>", methods=["GET"])
@auth_required
def get_anime(slug):
    result = {"error": None, "data": {}}

    anime = helpers.anime(slug)
    result["data"] = anime.dict(True)

    return result

@blueprint.route("/anime/watch/<string:slug>/<int:position>", methods=["GET"])
@auth_required
def watch_anime(slug, position):
    result = {"error": None, "data": {}}

    anime = helpers.anime(slug)
    index = AnimeService.position_index(anime, position)
    if index is None:
        return abort("episode", "not-found")

    result["data"] = anime.episodes[index].dict(True)
    return result

@blueprint.route("/anime/selected", methods=["GET"])
@auth_required
def selected_anime():
    result = {"error": None, "data": []}

    anime = AnimeService.selected()
    for item in anime:
        result["data"].append(item.dict())

    return result
