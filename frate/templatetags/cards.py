from django.template.library import Library, Node
from django import template


__all__ = [
    'customcard',
    'card_title',
    'card_body'
]


register = Library()


@register.tag
def customcard(parser, token):
    nodelist = parser.parse(('endcustomcard',))
    parser.delete_first_token()  # Remove 'endcustomcard' from the list of tokens.
    return CustomCardNode(nodelist)


class CustomCardNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        wrapped_output = f'<div class="card border w-fit m-2">{output}</div>'
        return wrapped_output


@register.tag(name='cardTitle')
def card_title(parser, token):
    try:
        tag_name, title = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    return CardTitleNode(title)


class CardTitleNode(Node):
    def __init__(self, title):
        self.title = template.Variable(title)

    def render(self, context):
        title_value = self.title.resolve(context)
        return f'<h3 class="text-indigo-400 text-xs uppercase">{title_value}</h3>'


@register.tag(name='cardBody')
def card_body(parser, token):
    try:
        tag_name, body_content = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    return CardBodyNode(body_content)


class CardBodyNode(template.Node):
    def __init__(self, body_content):
        self.body_content = template.Variable(body_content)

    def render(self, context):
        body_value = self.body_content.resolve(context)
        return f'<p>{body_value}</p>'
