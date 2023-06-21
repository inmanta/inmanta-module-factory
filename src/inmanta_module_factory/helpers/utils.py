"""
    Copyright 2022 Inmanta

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Contact: code@inmanta.com
    Author: Inmanta
"""
import logging
import pathlib
import re
import subprocess
import sys
import tempfile

import inmanta
import inmanta.ast.type
import inmanta.module
import inmanta.parser.plyInmantaLex

from inmanta_module_factory.helpers import const

LOGGER = logging.getLogger(__name__)

assert inmanta.parser.plyInmantaLex.t_ID.__doc__ is not None, "Invalid lexer specifications"
"""
The value accessed in the assertion above is not part of the stable api of inmanta-core.
If this assertion fails, this is likely a compatibility issue with inmanta-core, this docstring
is expected to contain the regular expression that defines what is a valid ID token.  If
it has been moved, the value can be set directly in the re.Pattern[str] object below.
"""

INMANTA_ID_TOKEN_EXPR = re.compile(inmanta.parser.plyInmantaLex.t_ID.__doc__)


def no_hyphen(name: str, *, force: bool = False) -> str:
    """
    Ensure that there is no hyphen in the provided name.  If force is set to True, replace
    any hyphen found with an underscore.

    :param name: The name to validate, and possibly convert
    :param force: Whether the name should be converted into the closest
        correct thing if it is not correct.
    """
    if "-" in name:
        if force:
            return name.replace("-", "_")

        raise ValueError(f"{repr(name)} is not a valid name: it can not contain an hyphen")

    return name


def validate_t_id_expression(name: str) -> str:
    """
    Ensure that the provided name matches the id expression.  Raise a ValueError if it is
    not a match.

    :param name: The name that should be a match.
    """
    if not INMANTA_ID_TOKEN_EXPR.fullmatch(name):
        # Id tokens should match the following expression:
        # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
        # /src/inmanta/parser/plyInmantaLex.py#L101
        raise ValueError(
            f"{repr(name)} is not a valid ID token: it doesn't match the expression {INMANTA_ID_TOKEN_EXPR.pattern}"
        )

    return name


def validate_id_token(name: str, *, force: bool = False) -> str:
    """
    Make sure the given name is a valid id token (parser scope) and returns the valid name
    or raise an exception if the name is not valid and force is set to false.

    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/parser/plyInmantaLex.py#L100

    :param name: The name to validate, and possibly convert
    :param force: Whether the name should be converted into the closest
        correct thing if it is not correct.
    """
    name = validate_t_id_expression(name)

    if name[0].isupper():
        # If the id starts with a capital letter, it is actually a CID token
        # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
        # /src/inmanta/parser/plyInmantaLex.py#L104
        if force:
            return validate_id_token(name.capitalize(), force=force)

        raise ValueError(f"{repr(name)} is not a valid ID token: ID tokens should start with a lower case letter")

    # Identifiers can not contain hyphens
    name = no_hyphen(name, force=force)

    if name in inmanta.parser.plyInmantaLex.reserved:
        # Reserved keywords generate their own token, they can't be used as id
        # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
        # /src/inmanta/parser/plyInmantaLex.py#L102
        raise ValueError(f"{repr(name)} is not a valid ID token: it matches a reserved keyword")

    return name


def validate_entity_name(name: str, *, force: bool = False) -> str:
    """
    Make sure that the given name would be a valid entity name for the parser and the
    compiler.  Return the valid name or raise an exception if the name is not valid
    and force is set to false.

    https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
    /src/inmanta/parser/plyInmantaParser.py#L281
    https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
    /src/inmanta/ast/statements/define.py#L117

    :param name: The name to validate, and possibly convert
    :param force: Whether the name should be converted into the closest
        correct thing if it is not correct.
    """
    name = validate_t_id_expression(name)

    if not name[0].isupper():
        # CID tokens should start with a capital letter
        # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
        # /src/inmanta/parser/plyInmantaLex.py#L104
        if force:
            return validate_entity_name(name[0].lower() + name[1:], force=force)

        raise ValueError(f"{repr(name)} is not a valid entity name: entity names should start with a capital letter")

    # Entity names can not contain hyphens
    # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
    # /src/inmanta/ast/statements/define.py#L135
    name = no_hyphen(name, force=force)

    return name


def validate_attribute_name(name: str, *, force: bool = False) -> str:
    """
    Make sure that the given name would be a valid attribute name for the parser and
    the compiler.  Return the valid name or raise an exception if the name is not valid
    and force is set to false.

    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/parser/plyInmantaParser.py#L371
    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/ast/statements/define.py#L94

    :param name: The name to validate, and possibly convert
    :param force: Whether the name should be converted into the closest
        correct thing if it is not correct.
    """

    # Overwrite the logic of validate_id_token to support a meaningful force
    # operation
    if name in inmanta.parser.plyInmantaLex.reserved:
        # Reserved keywords generate their own token, they can't be used as id
        # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
        # /src/inmanta/parser/plyInmantaLex.py#L102
        if force:
            return validate_attribute_name(name + "_", force=force)

        raise ValueError(f"{repr(name)} is not a valid attribute name: it matches a reserved keyword")

    # An attribute name should be a valid id token
    return validate_id_token(name, force=force)


def validate_relation_name(name: str, *, force: bool = False) -> str:
    """
    Make sure that the given name would be a valid relation name for the parser and the
    compiler.  Return the valid name or raise an exception if the name is not valid
    and force is set to false.

    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/parser/plyInmantaParser.py#L570
    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/ast/statements/define.py#L478

    :param name: The name to validate, and possibly convert
    :param force: Whether the name should be converted into the closest
        correct thing if it is not correct.
    """
    # The validation is actually the same as for the attribute
    return validate_attribute_name(name, force=force)


def validate_typedef_name(name: str, *, force: bool = False) -> str:
    """
    Make sure that the given name would be a valid type definition name for the parser
    and the compiler.  We can obviously not check here that no other type with the same
    name is defined in the same scope.  Return the valid name or raise an exception if
    the name is not valid and force is set to false.

    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/parser/plyInmantaParser.py#L629
    https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
    /src/inmanta/ast/statements/define.py#L398

    :param name: The name to validate, and possibly convert
    :param force: Whether the name should be converted into the closest
        correct thing if it is not correct.
    """
    # Overwrite the logic of validate_id_token to support a meaningful force
    # operation
    if name in inmanta.parser.plyInmantaLex.reserved:
        # Reserved keywords generate their own token, they can't be used as id
        # https://github.com/inmanta/inmanta-core/blob/808b4e99443d7c5009d7b9489649cbd452444ac3
        # /src/inmanta/parser/plyInmantaLex.py#L102
        if force:
            return validate_typedef_name(name + "_t", force=force)

        raise ValueError(f"{repr(name)} is not a valid typedef name: it matches a reserved keyword")

    # A typedef name should be a valid id token
    name = validate_id_token(name, force=force)

    if name in inmanta.ast.type.TYPES:
        # Typedef names can not match any of the existing primitive types
        # https://github.com/inmanta/inmanta-core/blob/c9fb88421a43bc967d4d36401c90d948e8d7171f
        # /src/inmanta/ast/statements/define.py#L421
        if force:
            return validate_typedef_name(name + "_t", force=force)

        raise ValueError(f"{repr(name)} is not a valid typdef name: it matches the name of an existing primitive type")

    return name


camel_case_regex = re.compile(r"(?<!^)(?=[A-Z])")


def camel_case_to_snake_case(input: str) -> str:
    """
    Converts a camel case string to snake case
    """
    return camel_case_regex.sub("_", input).lower()


def inmanta_entity_name(input: str) -> str:
    """
    Convert any string in a more conventional entity name.
    """
    return "".join([part.capitalize() for part in inmanta_safe_name(input).split("_")])


def inmanta_safe_name(input: str) -> str:
    """
    This helper method converts any string passed in input as a string
    that can safely be used as attribute name, relation name or module
    name.
    """
    output = input.replace("-", "_", -1).replace(".", "_", -1)
    try:
        int(output[0])
        output = f"x_{output}"
    except ValueError:
        pass

    # Attribute names can not start with a capital letter
    if output[0].upper() == output[0]:
        output = f"x_{output}"

    # Is it an inmanta keyword?
    if output in const.INMANTA_RESERVED_KEYWORDS:
        output = f"x_{output}"

    return output


def copyright_header_from_module(existing_module: inmanta.module.Module) -> str:
    """
    This helper function can help build a template header from an already existing module.
    So that it is used by the generator when the module is extended for example.
    """
    copyright_header_tmpl = None
    copyright_header_source_file = pathlib.Path(existing_module.path, existing_module.MODEL_DIR, "_init.cf")
    if not copyright_header_source_file.exists() or not copyright_header_source_file.is_file():
        raise ValueError(f"The path {copyright_header_source_file} doesn't point to a file.")

    model_root_content = copyright_header_source_file.read_text()
    docstring_blocks = model_root_content.split('"""')
    if not docstring_blocks:
        raise ValueError(f"Failed to extract copyright header from file {copyright_header_source_file}")

    copyright_header_tmpl = '"""' + docstring_blocks[1] + '"""'
    return copyright_header_tmpl


def fix_module_linting(existing_module: inmanta.module.Module) -> None:
    """
    Fix the linting of an existing (generated or not) module.
    """
    # Setup a virtual env, install dev dependencies and fix module linting
    with tempfile.TemporaryDirectory() as tmpdir:
        fix_linting_command = [
            "bash",
            "-c",
            (
                f"{sys.executable} -m venv {tmpdir}; "
                f"source {tmpdir}/bin/activate; "
                "pip install -U pip; "
                "pip install -r requirements.dev.txt; "
                f"black tests {existing_module.get_plugin_dir()}; "
                f"isort tests {existing_module.get_plugin_dir()}; "
                f"flake8 tests {existing_module.get_plugin_dir()}"
            ),
        ]
        LOGGER.debug(f"Running command {fix_linting_command}")
        result = subprocess.Popen(
            args=fix_linting_command,
            cwd=existing_module.path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = result.communicate()
        LOGGER.debug(stdout)
        LOGGER.debug(stderr)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fix the linting of the module (return code = {result.returncode}):\n{stderr}")


def remove_watermarked_files(directory: pathlib.Path) -> None:
    """
    Recursively traverse the directory and remove all files containing the "generated file"
    watermark.  If an empty folder is found, it is removed as well.
    """
    for file in directory.glob("*"):
        if file.is_dir():
            remove_watermarked_files(file)

            try:
                # Tries to get the first file that is still in the folder
                # If no file can be found, a StopIteration will be raised
                # and we know we can delete the full folder.
                next(file.glob("*"))
            except StopIteration:
                file.rmdir()

            continue

        if not (file.name.endswith(".py") or file.name.endswith(".cf")):
            # The file is not safe to read and we wouldn't have added
            # a water mark in there
            continue

        if const.GENERATED_FILE_MARKER in file.read_text(encoding="utf-8"):
            file.unlink()
