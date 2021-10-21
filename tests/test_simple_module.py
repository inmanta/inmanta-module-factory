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
from pathlib import Path

from pytest_inmanta.plugin import Project

from inmanta_module_factory.builder import InmantaModuleBuilder
from inmanta_module_factory.inmanta.attribute import Attribute, InmantaPrimitiveList
from inmanta_module_factory.inmanta.entity import Entity
from inmanta_module_factory.inmanta.entity_relation import EntityRelation
from inmanta_module_factory.inmanta.implement import Implement
from inmanta_module_factory.inmanta.implementation import Implementation
from inmanta_module_factory.inmanta.index import Index
from inmanta_module_factory.inmanta.module import Module


def test_empty_module(project: Project) -> None:
    module = Module(name="test")
    module_builder = InmantaModuleBuilder(module, Path(project._test_project_dir) / "libs")

    module_builder.generate_module()

    project.compile("import test")


def test_basic_module(project: Project) -> None:
    module = Module(name="test")
    module_builder = InmantaModuleBuilder(module, Path(project._test_project_dir) / "libs")

    entity = Entity(
        "Test",
        path=[module.name],
        attributes=[
            Attribute(
                name="test",
                inmanta_type=InmantaPrimitiveList("string"),
                default="[]",
                description="This is a test list attribute",
            ),
            Attribute(
                name="test1",
                inmanta_type="string",
                description="This is a test attribute",
            ),
        ],
        description="This is a test entity",
    )

    implementation = Implementation(
        name="test",
        path=[module.name],
        entity=entity,
        content=f"std::print(self.{entity.attributes[1].name})",
        description="This is a test implementation",
    )

    implement = Implement(
        path=[module.name],
        implementation=implementation,
        entity=entity,
    )

    index = Index(
        path=[module.name],
        entity=entity,
        attributes=entity.attributes[1:2],
        description="This is a test index",
    )

    relation = EntityRelation(
        name="tests",
        path=[module.name],
        entity=entity,
        arity=(0, None),
        peer=EntityRelation(
            name="",
            path=[module.name],
            entity=entity,
            arity=(0, 0),
        ),
    )

    module_builder.add_module_element(entity)
    module_builder.add_module_element(implementation)
    module_builder.add_module_element(implement)
    module_builder.add_module_element(index)
    module_builder.add_module_element(relation)

    module_builder.generate_module()

    project.compile(
        """
            import test

            test::Test(
                test1="a",
                tests=test::Test(test1="b"),
            )
            a = test::Test[test1="a"]
        """,
        no_dedent=False,
    )

    assert "a" in (project.get_stdout() or "")
    assert "b" in (project.get_stdout() or "")
