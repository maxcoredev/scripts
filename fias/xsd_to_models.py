# python xsd_to_models.py XSD/AS_DEL_HOUSEINT_2_250_17_04_01_01.xsd

import xml.etree.ElementTree as ET

import sys

types = {
    'string': 'CharField',
    'date': 'DateField',
    'integer': 'PositiveIntegerField',
    'byte': 'PositiveIntegerField',
    'int': 'PositiveIntegerField',
}

attrs = {
    'maxLength': 'max_length',
    'length': 'max_length',
    'minLength': None,
}

ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

tree = ET.parse(sys.argv[1])
root = tree.getroot()

class_name = root.find('.//xs:sequence/xs:element', ns).attrib.get('name')
class_descr = root.find('.//xs:sequence/xs:element/xs:annotation/xs:documentation', ns).text

attributes = root.findall('.//xs:attribute', ns)

f_docstring = f''
f_attributes = f''

for el in attributes:

    properties = []

    name = el.attrib.get('name').lower()

    if el.attrib.get('use') == 'optional':
        properties.append('null=True')

    xsd_type = el.attrib.get('type')
    if xsd_type: 
        type = types[xsd_type.split(':')[1]]

    documentation = el.find('.//xs:documentation', ns).text

    restriction = el.find('.//xs:restriction', ns)
    if not restriction is None:

        xsd_type = restriction.attrib.get('base').split(':')[1]
        type = types[xsd_type]
        
        for attr in list(restriction):
            attr_name = attr.tag.split('}')[1]
            attr_value = attr.attrib.get('value')
            if xsd_type == 'string' and attr_name == 'length' and attr_value == '36':
                type = 'UUIDField'
            else:
                if attrs.get(attr_name):
                    properties.append(attrs.get(attr_name) + '=' + attr_value)

    properties = ', '.join(properties)

    f_attributes += f'    {name} = models.{type}({properties})\n'

    documentation = '\n        '.join(documentation.strip().split('\n'))

    f_docstring += f'    {name} - {documentation}\n'

print(f'class {class_name}(models.Model):\n    """\n    {class_descr}\n\n{f_docstring}    """\n\n' + f_attributes)