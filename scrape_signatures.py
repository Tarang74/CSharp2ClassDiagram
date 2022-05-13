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


def find_index(l: list[dict[str, list]], key: str) -> int:
    for i, dic in enumerate(l):
        if key in dic:
            return i


def find_files(directory: str) -> list[str]:
    list_of_files = []
    for path, subdirs, files in walk(directory):
        for name in files:
            if name.endswith(".cs"):
                list_of_files.append(f"{path}\{name}")

    return list_of_files


def scrape(filename: str, OUTPUT_JSON: dict[str, list[dict[str, list[dict[str, list[dict[str, list[str]]]]]]]]) -> dict[str, list[dict[str, list[dict[str, list[dict[str, list[str]]]]]]]]:
    # print(filename)
    source_code: str
    with open(filename, "r", encoding="utf8") as f:
        source_code = f.read()

    namespace = findall(r"namespace\s([\w\.]+)", source_code)[0]
    if not any(namespace in d for d in OUTPUT_JSON["Class Diagram"]):
        OUTPUT_JSON["Class Diagram"].append({f"{namespace}": []})

    namespace_index = find_index(
        OUTPUT_JSON["Class Diagram"], namespace)

    class_ = findall(
        r"(?:internal\s|public\s)(?:static\s|abstract\s|partial\s)?(?:class|interface)\s(?:[\w\.]+)",
        source_code)[0]
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
        r"(?:public\s|private\s|protected\s|internal\s)\s*(?:readonly\s|static\s)*(?:(?!class)(?!interface)[\w<>]+)\s+(?:(?!set)\w+)(?:\s*=\s*(?:new\s*)?[\w<>\(\)\"\/\s/.]*)?(?=;|\s*\n*\{)",
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
        r"(?:public\s|private\s|protected\s|internal\s)\s*[\s\w]*(?:\w+)\s*(?:<(?:[\w]*,\s?)*>)?\s*\(\s*(?:(?:ref\s|in\s|out\s)?\s*(?:[\w<>\[\]]+)\s+(?:\w+)\s*=?\s*[\w\"\'\[\]]+,?\n?\s*)*\)(?:\s*:\s*base\s*\((?:[\w\"\'\(\)]*,*\s*)*\))?",
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


def XML_element(element_id: int, parent_id: int, text: str,
                x: int, y: int, width: int, height: int,
                style: str, additional_style: str = "") -> str:
    return f"        <mxCell id=\"{element_id}\" value=\"{escape(text)}\" style=\"{style}{additional_style}\" parent=\"{parent_id}\" vertex=\"1\">\n \
          <mxGeometry x=\"{x}\" y=\"{y}\" width=\"{width}\" height=\"{height}\" as=\"geometry\" />\n \
       </mxCell>\n"


def count_members(l: list[dict[str, list[str]]]) -> list[int]:
    fields = 0
    methods = 0

    for member in l:
        for member_key, member_items in member.items():
            if member_key == "Fields":
                fields = len(member_items)
            elif member_key == "Methods":
                methods = len(member_items)

    return (fields, methods)


def convert_to_XML(OUTPUT_JSON: dict[str, list[
    dict[str, list[
        dict[str, list[
            dict[str, list[str]]
        ]]
    ]]
]]
) -> str:
    OUTPUT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2022-05-13T08:33:25.475Z" type="device" agent="5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36" version="18.0.3">
  <diagram>
    <mxGraphModel dx="2000" dy="2000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
"""

    x = 100
    y = 100

    height = 26
    width = 400
    line_height = 8

    style_class = "swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;"
    style_interface = "swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;"
    style_member = "text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
    style_line = "line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;"

    style_bold = "fontStyle=1;"
    style_italics = "fontStyle=2;"
    style_underline = "fontStyle=4;"

    element_count = 2
    element_parent_count = 2

    for namespaces in OUTPUT_JSON["Class Diagram"]:
        for namespace_key, classes in namespaces.items():
            for class_ in classes:
                for class_key, members in class_.items():
                    print("-"*40)
                    (fields, methods) = count_members(members)
                    if (fields == 0 or methods == 0):
                        total_height = (1 + fields + methods) * height
                    else:
                        total_height = (1 + fields + methods) * height + line_height

                    current_class = ""
                    
                    if "class" in class_key:
                        text = class_key.split()[-1]
                        additional_style = ""
                            
                        if "static" in class_key:
                            additional_style += style_underline
                        elif "abstract" in class_key:
                            additional_style += style_italics

                        current_class = text
                        print(text)
                        OUTPUT_XML += XML_element(element_count, 1,
                                                  text, x, y, width,
                                                  total_height, style_class,
                                                  additional_style)

                    elif "interface" in class_key:
                        text = f"<<interface>><br />\n{class_key.split()[-1]}"
                        additional_style = ""

                        if "static" in class_key:
                            additional_style += style_underline
                        elif "abstract" in class_key:
                            additional_style += style_italics

                        current_class = text
                        print(text)
                        OUTPUT_XML += XML_element(element_count, 1,
                                                  text, x, y, width,
                                                  total_height,
                                                  style_interface,
                                                  additional_style)

                    y += height
                    element_count += 1

                    line_drawn = False
                    for member in members:
                        for member_key, member_signatures in member.items():
                            VISIBILITY = ["public", "internal", "protected", "private"]
                            VISIBILITY_SYMBOL = ['+', '~', '#', '-']
                            if member_key == "Fields":
                                for field_signature in member_signatures:
                                    text = ""

                                    # Visibility
                                    visibility = [x in field_signature for x in VISIBILITY]
                                    for i, v in enumerate(visibility):
                                        if v:
                                            text += VISIBILITY_SYMBOL[i]
                                    
                                    # Field
                                    field_search = findall(r"(?:(?:internal|public|protected|private|readonly|static|override)\s)*(?:([^\s]+)\s+([^\s]+))\s*(?:=\s*(.*))?", field_signature)[0]
                                    field_identifier = field_search[1].strip()
                                    field_default_value = field_search[2].strip()
                                    field_type = field_search[0].strip()

                                    text += f"{field_identifier} : {field_type}"

                                    if field_default_value:
                                        if "new" in field_default_value and "()" in field_default_value:
                                            text += f" = {field_type}"
                                        else:
                                            text += f" = {field_default_value}"

                                    # Property modifier
                                    abstract = any(x in field_signature for x in ["abstract", "virtual"])
                                    override = "override" in field_signature
                                    readonly = "readonly" in field_signature

                                    property_modifier = []
                                    if abstract:
                                        property_modifier.append("abstract")
                                    if readonly:
                                        property_modifier.append("readOnly")
                                    if override:
                                        property_modifier.append("redefines")

                                    if property_modifier:
                                        text += f" {{ {', '.join(property_modifier)} }}"

                                    additional_style = ""
                                    if "static" in field_signature:
                                        additional_style += style_underline
                                    
                                    print(text)
                                    OUTPUT_XML += XML_element(
                                        element_count, element_parent_count, text, x, y,
                                        width, height, style_member,
                                        additional_style)
                                    
                                    y += height
                                    element_count += 1

                            elif member_key == "Methods":
                                for method_signature in member_signatures:
                                    text = ""

                                    # Visibility
                                    visibility = [x in method_signature for x in VISIBILITY]
                                    for i, v in enumerate(visibility):
                                        if v:
                                            text += VISIBILITY_SYMBOL[i]

                                    method_search = findall(r"(?:(?:internal|public|protected|private|readonly|static|override|virtual|abstract)\s)*(?:([^\s()]+)\s+([^\n:]+))", method_signature)[0]
                                    method_identifier = method_search[1].strip()
                                    method_return_type = method_search[0].strip()

                                    if method_return_type == "void" or method_identifier.startswith(current_class):
                                        text += f"{method_identifier}"
                                    else:
                                        text += f"{method_identifier} : {method_return_type}"

                                    # Property modifier
                                    abstract = any(x in method_signature for x in ["abstract", "virtual"])
                                    override = "override" in method_signature
                                    
                                    property_modifier = []
                                    if readonly:
                                        property_modifier.append("readOnly")
                                    if override:
                                        property_modifier.append("redefines")

                                    if property_modifier:
                                        text += f" {{ {', '.join(property_modifier)} }}"

                                    additional_style = ""
                                    if "static" in method_signature:
                                        additional_style += style_underline

                                    print(text)
                                    OUTPUT_XML += XML_element(
                                        element_count, element_parent_count, text, x, y,
                                        width, height, style_member,
                                        additional_style)
                                    
                                    y += height
                                    element_count += 1
                                element_count += 1

                        if fields and methods and not line_drawn:
                            line_drawn = True
                            OUTPUT_XML += XML_element(element_count,
                                                    element_parent_count,
                                                    "", x, y, width,
                                                    line_height,
                                                    style_line)
                            y += line_height
                            element_count += 1

                y += 50
                element_parent_count = element_count

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
    root = find_files(
        r".\\path\\to\\C#\\project")

    main(root, False, False, True)
