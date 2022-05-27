from re import findall, sub
from os import walk
from json import dumps
from html import escape

# {"Class Diagram": [
#     {"Namespace_name": [
#         {"Class_name": [
#             {"Fields": ["field_signature", ...]},
#             {"Methods": ["method_signature", ...]}
#         ]}, ...
#     ]}, ...
# ]}

VISIBILITY_NAMES = ["public", "internal", "protected", "private"]
VISIBILITY_VARIANTS = [
    set([0]),
    set([2, 1]),
    set([1]),
    set([2]),
    set([3, 2]),
    set([3])]
VISIBILITY_SYMBOLS = ["+", "#~", "~", "#", "-#", "-"]


def find_index(l: list[dict[str, list]], key: str) -> int:
    for i, dic in enumerate(l):
        if key in dic:
            return i


def find_files(directory: str) -> list[str]:
    if not directory: 
        raise ValueError("No directory was supplied.")

    list_of_files = []
    for path, subdirs, files in walk(directory):
        for name in files:
            if name.endswith(".cs") and not path.startswith(f"{directory}\obj"):
                list_of_files.append(f"{path}\{name}")

    return list_of_files


def scrape(filename: str, OUTPUT_JSON: dict[str, list[dict[str, list[dict[str, list[dict[str, list[str]]]]]]]]) -> dict[str, list[dict[str, list[dict[str, list[dict[str, list[str]]]]]]]]:
    # print(filename)
    source_code: str
    with open(filename, "r", encoding="utf8") as f:
        source_code = f.read()

    try:
        namespace = findall(r"namespace\s*([\w\.]+)", source_code)[0]
    except IndexError:
        raise Exception(f"Could not find namespace in {filename}")

    if not any(namespace in d for d in OUTPUT_JSON["Class Diagram"]):
        OUTPUT_JSON["Class Diagram"].append({f"{namespace}": []})

    namespace_index = find_index(
        OUTPUT_JSON["Class Diagram"], namespace)

    try:
        class_ = findall(
            r"(?:internal\s|public\s|private\s)(?:static\s|abstract\s|partial\s)?(?:class|interface)\s*(?:[\w\.]+)",
            source_code)[0]
    except IndexError:
        raise Exception(f"Could not find class in {filename}")

    class_ = sub(r"\n", r" ", class_)
    class_ = sub(
        r"[\s]{2,}", r" ", class_).strip()
    OUTPUT_JSON["Class Diagram"][namespace_index][namespace].append({
                                                                    f"{class_}": []})

    class_index = find_index(
        OUTPUT_JSON["Class Diagram"]
        [namespace_index][namespace],
        class_)

    # print(namespace)
    # print(class_)
    # print("-" * 40)

    field_and_method_counter = 0

    fields = findall(
        r"(?:public\s|private\s|protected\s|internal\s)\s*(?:readonly\s|static\s|const\s|new\s)*(?:(?!class)(?!interface)[\w<>]+)\s+(?:(?!set)\w+)(?:\s*=\s*(?:new\s*)?[\w<>\(\)\"\/\s.]*)?(?=;|\s*\n*\{)",
        source_code)
    if fields:
        OUTPUT_JSON["Class Diagram"][namespace_index][namespace][
            class_index][class_].append({"Fields": []})
        for field in fields:
            field_cleaned = sub(r"\n", r" ", field)
            field_cleaned = sub(
                r"[\s]{2,}", r" ", field_cleaned).strip()
            OUTPUT_JSON["Class Diagram"][namespace_index][namespace][class_index][
                class_][field_and_method_counter]["Fields"].append(field_cleaned)

        field_and_method_counter += 1

    methods = findall(
        r"(?:public\s|private\s|protected\s|internal\s)\s*[\s\w]*(?:[\w<>]+)\s*(?:<(?:[\w]*,\s?)*>)?\s*\(\s*(?:(?:ref\s|in\s|out\s)?\s*(?:[\w<>\[\]]+)\s+(?:\w+)\s*=?\s*[\w\"\'\[\]]+,?\n?\s*)*\)(?:\s*:\s*base\s*\((?:[\w\"\'\(\)]*,*\s*)*\))?",
        source_code)
    if methods:
        OUTPUT_JSON["Class Diagram"][namespace_index][namespace][
            class_index][class_].append({"Methods": []})

        for method in methods:
            method_cleaned = sub(r"\n", r" ", method)
            method_cleaned = sub(
                r"[\s]{2,}", r" ", method_cleaned).strip()
            OUTPUT_JSON["Class Diagram"][namespace_index][namespace][class_index][
                class_][field_and_method_counter]["Methods"].append(method_cleaned)

    return OUTPUT_JSON


def convert_to_md(
    OUTPUT_JSON:
    dict[str, list[
         dict[str, list[
             dict[str, list[
                 dict[str, list[str]]
             ]]
         ]]
         ]]
) -> str:

    OUTPUT_MD = "# Class Diagram\n\n"

    for namespaces in OUTPUT_JSON["Class Diagram"]:
        for namespace_key, classes in namespaces.items():
            OUTPUT_MD += f"<!-- {namespace_key} {'-' * (47 - (len(namespace_key) + 1))} -->\n\n"

            for class_ in classes:
                for class_key, members in class_.items():
                    OUTPUT_MD += f"## {class_key}\n\n"

                    for member in members:
                        for member_key, member_signatures in member.items():
                            OUTPUT_MD += f"### {class_key}.{member_key}\n\n"

                            for member_signature in member_signatures:
                                OUTPUT_MD += f"{member_signature}\n"
                            OUTPUT_MD += "\n"

    return OUTPUT_MD


def XML_value_class(
        title: str, interface: bool, abstract: bool, static: bool) -> str:
    value = ""

    title_with_styles: str
    if static and abstract:
        title_with_styles = f"&lt;u&gt;&lt;i&gt;{title}&lt;/i&gt;&lt;/u&gt;"
    elif static:
        title_with_styles = f"&lt;u&gt;{title}&lt;/u&gt;"
    elif abstract:
        title_with_styles = f"&lt;i&gt;{title}&lt;/i&gt;"
    else:
        title_with_styles = title

    if interface:
        value = f"&lt;p style=&quot;margin-top:4px;margin-bottom:4px;text-align:center;&quot;&gt; \
                &lt;i&gt; \
                    &amp;lt;&amp;lt;Interface&amp;gt;&amp;gt; \
                &lt;/i&gt; \
                &lt;br&gt; \
                &lt;b&gt;{title_with_styles}&lt;/b&gt; \
            &lt;/p&gt;"
    else:
        value = f"&lt;p style=&quot;margin-top:4px;margin-bottom:4px;text-align:center;&quot;&gt; \
                &lt;b&gt;{title_with_styles}&lt;/b&gt; \
            &lt;/p&gt;"
    return value


def XML_value_field(field: list[str]) -> str:
    value = "&lt;p style=&quot;margin-top:4px;margin-bottom:4px;margin-left:4px;&quot;&gt;"
    # field: [name:str, type:str, visibility:str, static:bool, default_value:str, modifiers:str]
    if field[3]:
        value += f"{field[2]} &lt;u&gt;{field[0]}&lt;/u&gt;: {field[1]}{field[4]} {field[5]}"
    else:
        value += f"{field[2]} {field[0]}: {field[1]}{field[4]} {field[5]}"
    value += "&lt;/p&gt;"
    return value


def XML_value_method(method: list[str]) -> str:
    value = "&lt;p style=&quot;margin-top:4px;margin-bottom:4px;margin-left:4px;&quot;&gt;"

    # method: [name:str, parameters:str, return_type:str, visibility:str, static:bool, modifiers:str]
    if method[4]:
        if method[2]:
            value += f"{method[3]} &lt;u&gt;{method[0]}&lt;/u&gt;({method[1]}): {method[2]} {method[5]}"
        else:
            value += f"{method[3]} &lt;u&gt;{method[0]}&lt;/u&gt;({method[1]}) {method[5]}"
    else:
        if method[2]:
            value += f"{method[3]} {method[0]}({method[1]}): {method[2]} {method[5]}"
        else:
            value += f"{method[3]} {method[0]}({method[1]}) {method[5]}"

    value += "&lt;/p&gt;"
    return value

def parse_params(params: str) -> str:
    if params == "":
        return ""
    comma_separated = params.split(',')
    out = ""

    for i, parameter in enumerate(comma_separated):
        # print(parameter)
        matches = findall(r"([\w&;\[\]\(\)\{\}]+) ([\w\d_]+)( = .*$)?", parameter)[0]
        # print(matches)
        param_type = matches[0]
        param_identifier = matches[1]
        
        param_default = matches[2] if len(matches) == 3 else ""

        if i == len(comma_separated) - 1:
            out += f"{param_identifier}: {param_type}{param_default}"
        else:
            out += f"{param_identifier}: {param_type}{param_default}, "

    return out

def XML_element(element_id: int, parent_id: int, value: str,
                x: int, y: int, width: int, height: int,
                styles: str = "") -> str:
    return f"        <mxCell id=\"{element_id}\" value=\"{value}\" style=\"vertical-align=middle;align=left;overflow=fill;fontSize=12;fontFamily=Helvetica;html=1;{styles}\" parent=\"{parent_id}\" vertex=\"1\">\n \
          <mxGeometry x=\"{x}\" y=\"{y}\" width=\"{width}\" height=\"{height}\" as=\"geometry\" />\n \
       </mxCell>\n"


def convert_to_XML(OUTPUT_JSON: dict[str, list[
    dict[str, list[
        dict[str, list[
            dict[str, list[str]]
        ]]
    ]]
]]
) -> str:
    OUTPUT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2022-05-13T08:33:25.475Z" type="device" agent="5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36" version="18.0.3" etag="3d7OXHVQLkoMDTyIV0tP">
  <diagram id="Z7huS8_CQf_3WdyO0GcB">
    <mxGraphModel dx="2000" dy="2000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
"""

    x = 100
    y = 100

    # Choose arbitrary width
    width = 400

    # Height of various elements
    y_margin = 4
    line_height = 22
    rule_height = 1

    # Keep track of parent
    element_id = 2
    parent_id = 2

    style_class: str
    style_member = "text;strokeColor=none;fillColor=none;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
    style_line = "line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;"

    for namespaces in OUTPUT_JSON["Class Diagram"]:
        for namespace_key, classes in namespaces.items():
            for class_ in classes:
                for class_key, members in class_.items():
                    print("-" * 40)
                    relative_x = 0
                    relative_y = 0

                    # Class/interface info
                    class_name = class_key.split()[-1]
                    is_interface = "interface" in class_key
                    is_static = "static" in class_key
                    is_abstract = "abstract" in class_key

                    print(class_name)

                    # field: [name:str, type:str, visibility:str, static:bool, default_value:str, modifiers:str]
                    fields = []
                    # method: [name:str, parameters:str, return_type:str, visibility:str, static:bool, modifiers:str]
                    methods = []

                    for member in members:
                        for member_key, member_signatures in member.items():
                            if member_key == "Fields":
                                # Fields
                                for field_signature in member_signatures:
                                    field_name: str
                                    field_type: str
                                    field_visibility: list[str]
                                    field_static = any(x in field_signature for x in ["static", "const"])
                                    field_default_value = ""
                                    field_modifiers = ""

                                    # Field name
                                    field_search = findall(
                                        r"(?:(?:internal|public|protected|private|readonly|static|override|const|new)\s)*(?:([^\s]+)\s+([^\s]+))\s*(?:=\s*(.*))?",
                                        field_signature)[0]

                                    field_name = field_search[1].strip(
                                    )
                                    field_default_value = escape(
                                        field_search[2].strip())
                                    field_type = escape(
                                        field_search[0].strip())
                                    print(field_name)

                                    if field_default_value:
                                        if "new" in field_default_value and "()" in field_default_value:
                                            field_default_value = f" = {field_default_value[3:]}"
                                        else:
                                            field_default_value = f" = {field_default_value}"

                                    # Escape any additional <>
                                    field_type = escape(field_type)
                                    field_default_value = escape(field_default_value)

                                    # Field visibility
                                    v = []
                                    for i, V in enumerate(
                                            VISIBILITY_NAMES):
                                        if V in field_signature:
                                            v.append(i)
                                    for i, V in enumerate(
                                            VISIBILITY_VARIANTS):
                                        if set(v) == V:
                                            field_visibility = VISIBILITY_SYMBOLS[i]

                                    # Property modifiers
                                    abstract = any(
                                        x in field_signature
                                        for x
                                        in ["abstract", "virtual"])
                                    override = "override" in field_signature
                                    readonly = any(x in field_signature for x in ["readonly", "const"])

                                    property_modifier = []
                                    if abstract:
                                        property_modifier.append(
                                            "abstract")
                                    if readonly:
                                        property_modifier.append(
                                            "readOnly")
                                    if override:
                                        property_modifier.append(
                                            f"redefines {field_name}")

                                    if property_modifier:
                                        field_modifiers = f"{{ {', '.join(property_modifier)} }}"

                                    # Append to main list
                                    fields.append(
                                        [field_name, field_type,
                                         field_visibility,
                                         field_static,
                                         field_default_value,
                                         field_modifiers])

                            elif member_key == "Methods":
                                # Methods
                                for method_signature in member_signatures:
                                    method_name: str
                                    method_parameters: str
                                    method_return_type: str
                                    method_visibility: list[str]
                                    method_static = "static" in method_signature
                                    method_modifiers = ""

                                    # Method name
                                    method_search = findall(
                                        r"(?:(?:internal|public|protected|private|readonly|static|override|virtual|abstract|delegate)\s)*(?:([^\s()]+)\s+([^\n:]+))",
                                        method_signature)[0]

                                    method_identifier = method_search[1].strip(
                                    )

                                    method_identifier_split = method_identifier.split(
                                        "(", 1)
                                    method_name = escape(
                                        escape(
                                            method_identifier_split
                                            [0]))
                                    method_parameters = escape(
                                        escape(method_identifier_split[1][:-1]))

                                    method_parameters = parse_params(method_parameters)

                                    method_return_type = escape(
                                        escape(method_search[0].strip()))

                                    if method_return_type == "void" or method_name.startswith(class_name):
                                        method_return_type = ""

                                    print(f"{method_name}({method_parameters})")

                                    # Method visibility
                                    v = []
                                    for i, V in enumerate(
                                            VISIBILITY_NAMES):
                                        if V in method_signature:
                                            v.append(i)
                                    for i, V in enumerate(
                                            VISIBILITY_VARIANTS):
                                        if set(v) == V:
                                            method_visibility = VISIBILITY_SYMBOLS[i]

                                    # Property modifiers
                                    abstract = any(
                                        x in method_signature
                                        for x
                                        in ["abstract", "virtual"])
                                    override = "override" in method_signature

                                    property_modifier = []
                                    if override:
                                        property_modifier.append(
                                            f"redefines {method_name}")

                                    if property_modifier:
                                        method_modifiers += f"{{ {', '.join(property_modifier)} }}"

                                    # Append to main list
                                    methods.append(
                                        [method_name,
                                         method_parameters,
                                         method_return_type,
                                         method_visibility,
                                         method_static,
                                         method_modifiers])

                    # Sort members by visibility
                    fields.sort(
                        key=lambda x: VISIBILITY_SYMBOLS.index(x[2]))
                    methods.sort(
                        key=lambda x: VISIBILITY_SYMBOLS.index(x[3]))

                    # Dimensions of diagram
                    total_height = 0
                    if is_interface:
                        total_height += line_height + (
                            line_height - 2 * y_margin)
                    else:
                        total_height += line_height
                    if fields:
                        total_height += len(fields) * line_height
                    if methods:
                        if fields:
                            total_height += rule_height + \
                                len(methods) * line_height
                        else:
                            total_height += len(methods) * line_height

                    # Class/interface
                    value_class = XML_value_class(
                        class_name, is_interface, is_abstract, is_static)

                    if is_interface:
                        style_class = "swimlane;childLayout=stackLayout;horizontal=1;startSize=36;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;"
                    else:
                        style_class = "swimlane;childLayout=stackLayout;horizontal=1;startSize=22;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;"

                    OUTPUT_XML += XML_element(element_id, 1,
                                              value_class, x, y, width,
                                              total_height, style_class)
                    if is_interface:
                        relative_y += line_height + 14
                    else:
                        relative_y += line_height

                    parent_id = element_id
                    element_id += 1

                    # Fields and methods
                    for field in fields:
                        value_field = XML_value_field(field)
                        OUTPUT_XML += XML_element(
                            element_id, parent_id, value_field,
                            relative_x, relative_y, width, line_height,
                            style_member)
                        relative_y += line_height
                        element_id += 1

                    if methods:
                        if fields:
                            OUTPUT_XML += XML_element(element_id,
                                                      parent_id, "",
                                                      relative_x,
                                                      relative_y, width,
                                                      rule_height,
                                                      style_line)
                            relative_y += rule_height
                            element_id += 1

                        for method in methods:
                            value_method = XML_value_method(method)
                            OUTPUT_XML += XML_element(element_id,
                                                      parent_id,
                                                      value_method,
                                                      relative_x,
                                                      relative_y, width,
                                                      line_height,
                                                      style_member)
                            relative_y += line_height
                            element_id += 1

                    y += total_height + 20

    OUTPUT_XML += "      </root>\n \
    </mxGraphModel>\n \
  </diagram>\n \
</mxfile>"
    return OUTPUT_XML


def main(
        files: list[str],
        output_json: bool, output_md: bool, output_xml: bool):
    OUTPUT_JSON: dict[str, list[dict[str, list[dict[str, list[dict[str, list[str]]]]]]]] = {
        "Class Diagram": []}

    for file in files:
        OUTPUT_JSON = scrape(file, OUTPUT_JSON)

    if output_json:
        with open("class_diagram.json", "w") as f:
            f.write(dumps(OUTPUT_JSON, indent=4))

    if output_md:
        OUTPUT_MD = convert_to_md(OUTPUT_JSON)
        with open("class_diagram.md", "w") as f:
            f.write(OUTPUT_MD)

    if output_xml:
        OUTPUT_XML = convert_to_XML(OUTPUT_JSON)
        with open("class_diagram.xml", "w") as f:
            f.write(OUTPUT_XML)


if __name__ == "__main__":
    root = find_files(r"path\\to\\solution")

    main(root, False, False, True)
