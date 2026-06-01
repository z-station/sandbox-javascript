from flask import Flask, abort, jsonify, render_template, request
from marshmallow import ValidationError

from app.schema import (
    BadRequestSchema,
    DebugSchema,
    RunSchema,
    ServiceExceptionSchema,
    TestsSchema,
)
from app.service.exceptions import ServiceException
from app.service.main import JavaScriptService


def create_app():
    app = Flask(__name__)

    @app.errorhandler(400)
    def bad_request_handler(ex: ValidationError):
        return BadRequestSchema().dump(ex), 400

    @app.errorhandler(500)
    def service_error_handler(ex: ServiceException):
        return ServiceExceptionSchema().dump(ex), 500

    @app.route("/", methods=["get"])
    def index():
        return render_template("index.html")

    @app.route("/health", methods=["get"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/run", methods=["post"])
    def run():
        schema = RunSchema()
        try:
            if not request.is_json:
                raise ValidationError({"_schema": ["Request body must be JSON."]})
            data = JavaScriptService.run(schema.load(request.get_json()))
        except ValidationError as ex:
            abort(400, ex)
        except ServiceException as ex:
            abort(500, ex)
        else:
            return schema.dump(data)

    @app.route("/debug/", methods=["post"])
    def debug():
        schema = DebugSchema()
        try:
            if not request.is_json:
                raise ValidationError({"_schema": ["Request body must be JSON."]})
            data = JavaScriptService.debug(schema.load(request.get_json()))
        except ValidationError as ex:
            abort(400, ex)
        except ServiceException as ex:
            abort(500, ex)
        else:
            return schema.dump(data)

    @app.route("/testing/", methods=["post"])
    def testing():
        schema = TestsSchema()
        try:
            if not request.is_json:
                raise ValidationError({"_schema": ["Request body must be JSON."]})
            data = JavaScriptService.testing(schema.load(request.get_json()))
        except ValidationError as ex:
            abort(400, ex)
        except ServiceException as ex:
            abort(500, ex)
        else:
            return schema.dump(data)

    return app


app = create_app()

