from typing import Any


class SchemaValidationError(Exception):
    pass


def validate_json_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(instance, dict):
            raise SchemaValidationError(f"{path} must be an object.")
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise SchemaValidationError(f"{path}.{key} is required.")
        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                validate_json_schema(value, properties[key], f"{path}.{key}")
            elif additional_properties is False:
                raise SchemaValidationError(f"{path}.{key} is not allowed.")
    elif schema_type == "array":
        if not isinstance(instance, list):
            raise SchemaValidationError(f"{path} must be an array.")
        item_schema = schema.get("items")
        if item_schema:
            for index, value in enumerate(instance):
                validate_json_schema(value, item_schema, f"{path}[{index}]")
    elif schema_type == "string":
        if not isinstance(instance, str):
            raise SchemaValidationError(f"{path} must be a string.")
    elif schema_type == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            raise SchemaValidationError(f"{path} must be an integer.")
    elif schema_type == "number":
        if not isinstance(instance, (int, float)) or isinstance(instance, bool):
            raise SchemaValidationError(f"{path} must be a number.")
    elif schema_type == "boolean":
        if not isinstance(instance, bool):
            raise SchemaValidationError(f"{path} must be a boolean.")
    elif schema_type is None:
        return
    else:
        raise SchemaValidationError(f"{path} uses unsupported schema type '{schema_type}'.")

