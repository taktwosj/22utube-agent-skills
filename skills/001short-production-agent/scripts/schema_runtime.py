from __future__ import annotations

import re
from typing import Any


TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def _resolve_local_ref(root_schema: dict, reference: str) -> dict | None:
    if not reference.startswith("#/"):
        return None
    value: Any = root_schema
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or token not in value:
            return None
        value = value[token]
    return value if isinstance(value, dict) else None


def validate_schema(
    instance: Any,
    schema: dict,
    path: str = "$",
    root_schema: dict | None = None,
) -> list[str]:
    if root_schema is None:
        root_schema = schema
    errors: list[str] = []
    reference = schema.get("$ref")
    if isinstance(reference, str):
        resolved = _resolve_local_ref(root_schema, reference)
        if resolved is None:
            errors.append(f"{path}: unresolved schema reference {reference}")
        else:
            errors.extend(validate_schema(instance, resolved, path, root_schema))
    conditional = schema.get("if")
    if isinstance(conditional, dict):
        branch = (
            schema.get("then")
            if not validate_schema(instance, conditional, path, root_schema)
            else schema.get("else")
        )
        if isinstance(branch, dict):
            errors.extend(validate_schema(instance, branch, path, root_schema))
    for index, subschema in enumerate(schema.get("allOf", [])):
        if isinstance(subschema, dict):
            errors.extend(
                validate_schema(instance, subschema, f"{path}.allOf[{index}]", root_schema)
            )
    expected = schema.get("type")
    if expected:
        allowed = TYPE_MAP.get(expected)
        if allowed is None:
            return [f"{path}: unsupported schema type {expected}"]
        if not isinstance(instance, allowed) or (
            expected in {"number", "integer"} and isinstance(instance, bool)
        ):
            return [f"{path}: expected {expected}"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is not in enum")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is too short")
        if schema.get("pattern") and not re.fullmatch(schema["pattern"], instance):
            errors.append(f"{path}: pattern mismatch")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value is below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: value is above maximum")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: array is too short")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: array is too long")
        if schema.get("uniqueItems") is True:
            for index, value in enumerate(instance):
                if value in instance[:index]:
                    errors.append(f"{path}: array items are not unique")
                    break
        contains_schema = schema.get("contains")
        if isinstance(contains_schema, dict) and not any(
            not validate_schema(value, contains_schema, f"{path}[{index}]", root_schema)
            for index, value in enumerate(instance)
        ):
            errors.append(f"{path}: no item matches contains")
        for index, item_schema in enumerate(schema.get("prefixItems", [])):
            if index < len(instance) and isinstance(item_schema, dict):
                errors.extend(
                    validate_schema(instance[index], item_schema, f"{path}[{index}]", root_schema)
                )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                errors.extend(validate_schema(value, item_schema, f"{path}[{index}]", root_schema))
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing {key}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                errors.extend(
                    validate_schema(value, properties[key], f"{path}.{key}", root_schema)
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected {key}")
    return errors
