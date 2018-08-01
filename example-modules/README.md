# Example Modules

This directory should have some example "modules", which are really just
"blueprints" that take extra arguments.

You must define the following:

- [A test fixture](#fixture)
- [A blueprint](#blueprint)

Once you do that, if you have butter installed you can run `butter-test` with no
argutments to see usage.

## Blueprint Fixture

Your module must contain a `blueprint_fixture` module or file that defines a
`BlueprintTest` class at the top level.  You should inherit from
`butter.testutils.fixture.BlueprintTestInterface` and implement all the required
methods.  Here's an example:

    from butter.testutils.blueprint_tester import generate_unique_name
    from butter.testutils.fixture import BlueprintTestInterface

    class BlueprintTest(BlueprintTestInterface):
        # Define all the required methods on this class.  See parent class for
        # details.

## Blueprint

The blueprint for the service you are testing should live at `blueprint.yml`.
This is a standard butter blueprint.  You must make sure that any required
template variables are properly returned by your test fixture.
