"""
    Copyright 2021 Inmanta

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
from typing import List, Optional, Set, Union
from typing_extensions import Literal

from inmanta_module_factory.inmanta.module_element import ModuleElement

InmantaPrimitiveType = Literal["string", "int", "number", "bool"]


class TypeDef(ModuleElement):
    def __init__(
        self,
        name: str,
        path: List[str],
        base_type: "InmantaBaseType",
        constraint: str,
        description: Optional[str] = None,
    ) -> None:
        """
        :param name: The name of this type definition
        :param path: The path to the location in this module where the typedef should be defined
        :param base_type: The base type this typedef adds constraints on
        :param constraint: The constraint to add to this typedef
        :param description: Some explanation about what this constraint does
        """
        super().__init__(name, path, description)
        self.base_type = base_type
        self.constraint = constraint

    def _ordering_key(self) -> str:
        return f"{chr(0)}.typedef.{self.name}"

    def _get_derived_imports(self) -> Set[str]:
        imports: Set[str] = set()

        if isinstance(self.base_type, TypeDef):
            if self.base_type.path != self.path:
                # Base type is defined in another file
                imports.add(self.base_type.path_string)

        return imports

    def __str__(self) -> str:
        base_type_expression = self.base_type.full_path_string if isinstance(self.base_type, TypeDef) else self.base_type

        stmt = f"typedef {self.name} as {base_type_expression} matching {self.constraint}"
        docstring = self.docstring()
        if docstring:
            docstring = f'"""\n{docstring}"""\n'

        return f"{stmt}\n{docstring}"


InmantaBaseType = Union[InmantaPrimitiveType, TypeDef]
