from typing import Optional

from marshmallow import Schema, ValidationError
from marshmallow.decorators import post_load, pre_dump
from marshmallow.fields import Boolean, Field, Integer, Method, Nested

from app.entities import DebugData, RunData, TestData, TestsData
from app.service.exceptions import ServiceException
from app.utils import clean_str


class StrField(Field):
    def _deserialize(self, value: Optional[str], *args, **kwargs):
        if value is not None and not isinstance(value, str):
            raise ValidationError("Not a valid string.")
        return clean_str(value)

    def _serialize(self, value: Optional[str], *args, **kwargs):
        return clean_str(value)


class StreamField(Field):
    def _serialize(self, value: Optional[str], *args, **kwargs):
        return value or ""


class CodeField(StrField):
    def _deserialize(self, value: Optional[str], *args, **kwargs):
        value = super()._deserialize(value, *args, **kwargs)
        if not value or not value.strip():
            raise ValidationError("Code must not be empty.")
        return value


class RunSchema(Schema):
    code = CodeField(required=True, load_only=True)
    stdout = StreamField(dump_only=True)
    stderr = StreamField(dump_only=True)
    exit_code = Integer(dump_only=True)

    @post_load
    def make_run_data(self, data, **kwargs) -> RunData:
        return RunData(**data)


class DebugSchema(Schema):
    data_in = StrField(required=False, allow_none=True, load_only=True)
    code = CodeField(required=True, load_only=True)
    result = StrField(dump_only=True)
    error = StrField(dump_only=True)
    exit_code = Integer(dump_only=True)

    @post_load
    def make_debug_data(self, data, **kwargs) -> DebugData:
        return DebugData(**data)


class TestSchema(Schema):
    data_in = StrField(load_only=True, allow_none=True)
    data_out = StrField(required=True, load_only=True)
    result = StrField(dump_only=True)
    error = StrField(dump_only=True)
    exit_code = Integer(dump_only=True)
    ok = Boolean(dump_only=True)

    @post_load
    def make_test_data(self, data, **kwargs) -> TestData:
        return TestData(**data)


class TestsSchema(Schema):
    tests = Nested(TestSchema, many=True, required=True)
    checker = StrField(load_only=True, required=True)
    code = CodeField(load_only=True, required=True)
    num = Integer(dump_only=True)
    num_ok = Integer(dump_only=True)
    ok = Boolean(dump_only=True)

    @post_load
    def make_tests_data(self, data, **kwargs) -> TestsData:
        return TestsData(**data)

    @pre_dump
    def calculate_properties(self, data: TestsData, **kwargs):
        data.num = len(data.tests)
        data.num_ok = 0
        for test in data.tests:
            if test.ok:
                data.num_ok += 1
        data.ok = data.num == data.num_ok
        return data


class BadRequestSchema(Schema):
    error = Method("dump_error")
    details = Method("dump_details")

    def dump_error(self, obj):
        return "Validation error"

    def dump_details(self, obj):
        return obj.description.messages


class ServiceExceptionSchema(Schema):
    error = Method("dump_error")
    details = Method("dump_details")

    def dump_error(self, obj):
        return obj.description.message

    def dump_details(self, obj):
        return obj.description.details
