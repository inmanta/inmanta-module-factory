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
from typing import Literal


class InmantaType:
    """
    Base class for all inmanta attribute type representations.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def path_string(self) -> str:
        """
        This returns the path of this entity's file in this module.  The name of the module
        is the first element of the path.
        """
        return ""

    @property
    def full_path_string(self) -> str:
        """
        This returns the path of this entity in this module.  The difference with path_string
        is that this one contains the name of the entity at the end.
        """
        return self.name

    def __str__(self) -> str:
        return self.name


class InmantaAdvancedType(InmantaType, str):
    def __init__(self, name: Literal["dict", "any"]) -> None:
        super().__init__(name)


InmantaDictType = InmantaAdvancedType("dict")
InmantaAnyType = InmantaAdvancedType("any")


class InmantaBaseType(InmantaType):
    def __init__(self, name: str) -> None:
        super().__init__(name)


class InmantaPrimitiveType(InmantaBaseType, str):
    def __init__(self, name: Literal["int", "bool", "number", "string"]) -> None:
        super().__init__(name)


InmantaIntegerType = InmantaPrimitiveType("int")
InmantaBooleanType = InmantaPrimitiveType("bool")
InmantaNumberType = InmantaPrimitiveType("number")
InmantaStringType = InmantaPrimitiveType("string")


class InmantaListType(InmantaType):
    def __init__(self, item_type: InmantaBaseType) -> None:
        super().__init__(item_type.name + "[]")
        self.item_type = item_type

    @property
    def path_string(self) -> str:
        """
        This returns the path of this entity's file in this module.  The name of the module
        is the first element of the path.
        """
        return self.item_type.path_string

    @property
    def full_path_string(self) -> str:
        """
        This returns the path of this entity in this module.  The difference with path_string
        is that this one contains the name of the entity at the end.
        """
        return self.item_type.full_path_string + "[]"
