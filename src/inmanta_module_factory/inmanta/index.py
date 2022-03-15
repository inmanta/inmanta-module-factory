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
from typing import List, Optional, Set

from inmanta_module_factory.inmanta.attribute import Attribute
from inmanta_module_factory.inmanta.entity import Entity
from inmanta_module_factory.inmanta.module_element import ModuleElement
from inmanta_module_factory.inmanta.entity_relation import EntityRelation


class Index(ModuleElement):
    def __init__(
        self,
        path: List[str],
        entity: Entity,
        *,
        attributes: Optional[List[Attribute]] = None,
        relations: Optional[List[EntityRelation]] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        An index statement.
        :param path: The place in the module where the index should be printed
        :param entity: The entity this index is applied to
        :param attributes: A portion of the entity attributes on which apply the index
        :param relations: A portion of the entity relations on which apply the index
        :param description: A description of the index, to be added as docstring
        """
        super().__init__("index", path, description)
        self.entity = entity
        self.attributes = attributes or []
        self.relations = relations or []

    @property
    def index_members(self) -> List[str]:
        index_members = [attribute.name for attribute in self.attributes]
        index_members += [relation.name for relation in self.relations]
        return index_members

    def _ordering_key(self) -> str:
        suffix = "_".join(self.index_members)
        if self.path_string != self.entity.path_string:
            return f"{chr(255)}.index.{self.entity.full_path_string}_{suffix}"

        return f"{self.entity.ordering_key}_{suffix}"

    def _get_derived_imports(self) -> Set[str]:
        imports = set()

        if self.path_string != self.entity.path_string:
            # Entity is in another file
            imports.add(self.entity.path_string)

        return imports

    def validate(self) -> bool:
        if len(self.attributes) + len(self.relations) == 0:
            return False

        if not len(set(self.attributes) - set(self.entity.attributes)) == 0:
            return False

        for relation in self.relations:
            if relation.entity != self.entity:
                return False

        return True

    def __str__(self) -> str:
        entity_path = self.entity.name
        if self.path_string != self.entity.path_string:
            # Entity is in another file
            entity_path = self.entity.full_path_string

        return f"index {entity_path}({', '.join(self.index_members)})\n"
