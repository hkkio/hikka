from hikka.services.permissions import PermissionsService
from hikka.services.types import ReleaseTypesService
from hikka.services.releases import ReleasesService
from hikka.services.genres import GenresService
from hikka.services.teams import TeamService
from hikka.services.users import UserService
from flask_restful import Resource
from flask_restful import reqparse
from hikka import errors

class NewRelease(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("description", type=str, default=None, required=True)
        parser.add_argument("slug", type=str, default=None, required=True)
        parser.add_argument("team", type=str, default=None, required=True)
        parser.add_argument("type", type=str, default=None, required=True)
        parser.add_argument("auth", type=str, default=None, required=True)
        parser.add_argument("title", type=dict, required=True)
        parser.add_argument("genres", type=list, default=[])
        args = parser.parse_args()

        title_parser = reqparse.RequestParser()
        title_parser.add_argument("ua", type=str, location=("title",))
        title_parser.add_argument("jp", type=str, default=None, location=("title",))
        title_args = title_parser.parse_args(req=args)

        result = {
            "error": errors.get("account", "not-found"),
            "data": {}
        }

        account = UserService.auth(args["auth"])

        if account is not None:
            result["error"] = errors.get("team", "not-found")
            team = TeamService.get_by_slug(args["team"])

            if team is not None:
                result["error"] = errors.get("account", "permission")

                if PermissionsService.check(account, f"team-{team.slug}", "admin"):
                    result["error"] = None

                    release = ReleasesService.get_by_slug(args["slug"])
                    if release is not None:
                        result["error"] = errors.get("release", "slug-exists")

                    rtype = ReleaseTypesService.get_by_slug(args["type"])
                    if rtype is None:
                        result["error"] = errors.get("type", "not-found")

                    if args["description"] is None:
                        result["error"] = errors.get("general", "missing-field")

                    genres = []
                    for slug in args["genres"]:
                        genre = GenresService.get_by_slug(slug)
                        if genre is not None:
                            genres.append(genre)

                        else:
                            result["error"] = errors.get("genre", "not-found")
                            break

                    if result["error"] is None:
                        title = ReleasesService.get_title(title_args["ua"], title_args["jp"])

                        release = ReleasesService.create(
                            title,
                            args["slug"],
                            args["description"],
                            rtype,
                            genres,
                            [team]
                        )

                        result["data"] = {
                            "title": release.title.dict(),
                            "description": release.description,
                            "type": release.rtype.slug,
                            "slug": release.slug
                        }

        return result
