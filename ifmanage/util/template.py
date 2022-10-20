import functools
import os

from jinja2 import FileSystemLoader, Environment, ChainableUndefined

from util.file import chmod, chown, makedir


# reuse Environments with identical settings to improve performance
@functools.lru_cache(maxsize=2)
def get_environment(location=None):
    loc_loader = FileSystemLoader(location)
    env = Environment(
        # Don't check if template files were modified upon re-rendering
        auto_reload=False,
        # Cache up to this number of templates for quick re-rendering
        cache_size=100,
        loader=loc_loader,
        trim_blocks=True,
        undefined=ChainableUndefined,
    )
    return env


def render(destination, template, content, formater=None, permission=None, user=None, group=None, location=None):
    """Render a template from the template directory to a file, raise on any errors.

    :param destination: path to the file to save the rendered template in
    :param template: the path to the template relative to the template folder
    :param content: the dictionary of variables to put into rendering context
    :param formater: if given, it has to be a callable the rendered string is passed through
    :param permission: permission bitmask to set for the output file
    :param user: user to own the output file
    :param group: group to own the output file
    :param location: the location of the template

    All other parameters are as for :func:`render_to_string`.
    """
    # Create the directory if it does not exist
    folder = os.path.dirname(destination)
    makedir(folder, user, group)

    # As we are opening the file with 'w', we are performing the rendering before
    # calling open() to not accidentally erase the file if rendering fails
    rendered = render_to_string(template, content, formater, location)

    # Write to file
    with open(destination, "w") as file:
        chmod(file.fileno(), permission)
        chown(file.fileno(), user, group)
        file.write(rendered)


def render_to_string(template, content, formater=None, location=None):
    """Render a template from the template directory, raise on any errors.

    :param template: the path to the template relative to the template folder
    :param content: the dictionary of variables to put into rendering context
    :param formater: if given, it has to be a callable the rendered string is passed through
    :param location: the location of the template

    The parsed template files are cached, so rendering the same file multiple times
    does not cause as too much overhead.
    If used everywhere, it could be changed to load the template from Python
    environment variables from an importable Python module generated when the Debian
    package is build (recovering the load time and overhead caused by having the
    file out of the code).
    """
    template = get_environment(location).get_template(template)
    rendered = template.render(content)
    if formater is not None:
        rendered = formater(rendered)
    return rendered
