import argparse
import enum
import importlib
from pathlib import Path


def format_ts_value(value: object) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_ts() -> str:
    enums_module = importlib.import_module("app.constants.enums")
    lines: list[str] = [
        "/* eslint-disable */",
        "// AUTO-GENERATED FILE. DO NOT EDIT.",
        "",
    ]

    exported_names: list[str] = []

    for name, obj in vars(enums_module).items():
        if not isinstance(obj, type):
            continue
        if not issubclass(obj, enum.Enum):
            continue
        if obj.__module__ != enums_module.__name__:
            continue

        exported_names.append(name)
        lines.append(f"export enum {name} {{")
        for member in obj:
            lines.append(f"  {member.name} = {format_ts_value(member.value)},")
        lines.append("}")
        lines.append("")

        values_name = f"{name}Values"
        lines.append(f"export const {values_name} = [")
        for member in obj:
            lines.append(f"  {format_ts_value(member.value)},")
        lines.append("] as const")
        lines.append("")

        type_name = f"{name}Value"
        lines.append(f"export type {type_name} = (typeof {values_name})[number]")
        lines.append("")

    if exported_names:
        lines.append("export const ENUM_NAMES = [")
        for enum_name in exported_names:
            lines.append(f'  "{enum_name}",')
        lines.append("] as const")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export backend enums to TypeScript")
    parser.add_argument("--out", required=True, help="Output TypeScript file path")
    args = parser.parse_args()

    output_path = Path(args.out).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_ts(), encoding="utf-8")
    print(f"[export-enums] generated {output_path}")


if __name__ == "__main__":
    main()
