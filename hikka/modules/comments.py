from hikka.services.comments import CommentService
from hikka.services.anime import AnimeService
from hikka.tools.parser import RequestParser
from hikka.decorators import auth_required
from datetime import datetime, timedelta
from flask.views import MethodView
from hikka.tools import helpers
from hikka.errors import abort
from flask import request

choices = ("anime")

def get_service(service):
    if service == "anime":
        return AnimeService

class NewComment(MethodView):
    @auth_required
    def post(self):
        result = {"error": None, "data": {}}

        parser = RequestParser()
        parser.argument("subject", type=str, required=True, choices=choices)
        parser.argument("text", type=helpers.string, required=True)
        parser.argument("slug", type=str, required=True)
        args = parser.parse()

        service = get_service(args["subject"])
        subject = service.get_by_slug(args["slug"])

        comment = CommentService.create(subject, request.account, args["text"])
        result["data"] = comment.dict()

        return result

class UpdateComment(MethodView):
    @auth_required
    def post(self):
        result = {"error": None, "data": {}}

        parser = RequestParser()
        parser.argument("counter", type=int, required=True)
        parser.argument("params", type=dict, default={})
        args = parser.parse()

        params_parser = RequestParser()
        params_parser.argument("text", type=helpers.string, required=True, location=("params"))
        params_args = params_parser.parse(req=args)

        comment = CommentService.get_by_counter(args["counter"], request.account)
        if comment is None:
            return abort("comment", "not-found")

        if datetime.now() - comment.created > timedelta(minutes=20):
            return abort("comment", "not-editable")

        comment.text = params_args["text"]
        comment.updated = datetime.now()
        comment.save()

        result["data"] = comment.dict()
        return result

class ListComments(MethodView):
    @auth_required
    def post(self):
        result = {"error": None, "data": []}

        parser = RequestParser()
        parser.argument("subject", type=str, required=True, choices=choices)
        parser.argument("slug", type=str, required=True)
        parser.argument("page", type=int, default=0)
        args = parser.parse()

        service = get_service(args["subject"])
        subject = service.get_by_slug(args["slug"])
        comments = CommentService.list(subject, args["page"])

        for comment in comments:
            result["data"].append(comment.dict())

        return result
