from hikka.services.permissions import PermissionsService
from hikka.services.types import ReleaseTypesService
from hikka.services.func import update_document
from hikka.services.users import UserService
from flask_restful import Resource
from flask_restful import reqparse
from hikka.errors import abort
from hikka import utils

class NewReleaseType(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, default=None, required=True)
        parser.add_argument("slug", type=str, default=None, required=True)
        parser.add_argument("auth", type=str, default=None, required=True)
        parser.add_argument("description", type=str, default=None)
        args = parser.parse_args()

        result = {"error": None, "data": {}}
        account = UserService.auth(args["auth"])

        if account is None:
            return abort("account", "not-found")

        if not PermissionsService.check(account, "global", "admin"):
            return abort("account", "permission")

        rtype = ReleaseTypesService.get_by_slug(args["slug"])
        if rtype is not None:
            return abort("type", "slug-exists")

        rtype = ReleaseTypesService.create(args["name"], args["slug"], args["description"])
        result["data"] = {
            "description": rtype.description,
            "name": rtype.name,
            "slug": rtype.slug
        }

        return result

class UpdateReleaseType(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("slug", type=str, default=None, required=True)
        parser.add_argument("auth", type=str, default=None, required=True)
        parser.add_argument("update", type=dict, default={})
        args = parser.parse_args()

        update_parser = reqparse.RequestParser()
        update_parser.add_argument("name", type=str, location=("update",))
        update_parser.add_argument("slug", type=str, location=("update",))
        update_parser.add_argument("description", type=str, location=("update",))
        update_args = update_parser.parse_args(req=args)

        result = {"error": None, "data": {}}
        account = UserService.auth(args["auth"])

        if account is None:
            return abort("account", "not-found")

        if not PermissionsService.check(account, "global", "admin"):
            return abort("account", "permission")

        rtype = ReleaseTypesService.get_by_slug(args["slug"])
        if rtype is None:
            return abort("type", "not-found")

        keys = ["name", "slug", "description"]
        update = utils.filter_dict(update_args, keys)
        update_document(rtype, update)

        result["data"] = {
            "description": rtype.description,
            "name": rtype.name,
            "slug": rtype.slug
        }

        return result
