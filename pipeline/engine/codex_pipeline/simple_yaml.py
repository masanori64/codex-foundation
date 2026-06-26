from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_structured_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return {}
    if stripped.startswith("{"):
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise ValueError(f"{path}: root must be an object")
        return parsed
    parsed = loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return parsed


def loads(text: str) -> Any:
    lines = _logical_lines(text)
    if not lines:
        return {}
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError(f"unexpected trailing line: {lines[index][1]}")
    return value


def dumps(value: Any, *, indent: int = 0) -> str:
    lines: list[str] = []
    _dump_value(lines, value, indent)
    return "\n".join(lines) + "\n"


def _logical_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if "\t" in raw:
            raise ValueError("tabs are not supported in YAML subset")
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))
    return lines


def _strip_comment(raw: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(raw):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return raw[:index]
    return raw


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    current_indent, text = lines[index]
    if current_indent < indent:
        return {}, index
    if current_indent != indent:
        raise ValueError(f"unexpected indentation for line: {text}")
    if text.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_mapping(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent:
            raise ValueError(f"unexpected mapping indentation for line: {text}")
        if text.startswith("- "):
            break
        key, value_text = _split_pair(text)
        if value_text:
            result[key] = _parse_scalar(value_text)
            index += 1
            continue
        index += 1
        if index >= len(lines) or lines[index][0] <= indent:
            result[key] = {}
            continue
        child, index = _parse_block(lines, index, lines[index][0])
        result[key] = child
    return result, index


def _parse_list(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not text.startswith("- "):
            break
        item_text = text[2:].strip()
        index += 1
        if not item_text:
            if index >= len(lines) or lines[index][0] <= indent:
                result.append(None)
                continue
            child, index = _parse_block(lines, index, lines[index][0])
            result.append(child)
            continue
        if ":" in item_text and not item_text.startswith(("'", '"')):
            key, value_text = _split_pair(item_text)
            item: dict[str, Any] = {}
            if value_text:
                item[key] = _parse_scalar(value_text)
            elif index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
                item[key] = child
            else:
                item[key] = {}
            if index < len(lines) and lines[index][0] > indent:
                child, index = _parse_block(lines, index, lines[index][0])
                if isinstance(child, dict):
                    item.update(child)
                else:
                    item["_items"] = child
            result.append(item)
            continue
        result.append(_parse_scalar(item_text))
    return result, index


def _split_pair(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"expected key/value pair: {text!r}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"empty key in line: {text!r}")
    return key, value.strip()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value[0] == value[-1:] and value.startswith(("'", '"')):
        return value[1:-1]
    lowered = value.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        return value


def _dump_value(lines: list[str], value: Any, indent: int) -> None:
    pad = " " * indent
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict | list):
                lines.append(f"{pad}{key}:")
                _dump_value(lines, item, indent + 2)
            else:
                lines.append(f"{pad}{key}: {_format_scalar(item)}")
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{pad}- {{}}")
                    continue
                first_key = next(iter(item))
                first_value = item[first_key]
                if isinstance(first_value, dict | list):
                    lines.append(f"{pad}- {first_key}:")
                    _dump_value(lines, first_value, indent + 4)
                else:
                    lines.append(f"{pad}- {first_key}: {_format_scalar(first_value)}")
                rest = {key: val for key, val in item.items() if key != first_key}
                _dump_value(lines, rest, indent + 2)
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                _dump_value(lines, item, indent + 2)
            else:
                lines.append(f"{pad}- {_format_scalar(item)}")
        return
    lines.append(f"{pad}{_format_scalar(value)}")


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, int | float):
        return str(value)
    text = str(value)
    if not text or any(char in text for char in [":", "#", "[", "]", "{", "}", "\n"]):
        return json.dumps(text, ensure_ascii=False)
    return text
