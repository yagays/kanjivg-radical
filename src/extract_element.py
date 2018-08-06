import json
import unicodedata
from pathlib import Path
from collections import defaultdict, Iterable

from xml.etree import ElementTree

kvg_url = "{http://kanjivg.tagaini.net}"
kvg_element_attrib = f"{kvg_url}element"
kvg_type_attrib = f"{kvg_url}type"
kvg_position_attrib = f"{kvg_url}position"


def find_all_element_and_type(g):
    if kvg_type_attrib in g.attrib:
        return g.get(kvg_type_attrib)
    if not kvg_type_attrib in g.attrib and not kvg_element_attrib in g.attrib:
        return [find_all_element_and_type(child) for child in g]

    return {g.get(kvg_element_attrib): [find_all_element_and_type(child) for child in g]}


def find_all_element(g):
    if kvg_type_attrib in g.attrib:
        return ""
    if not kvg_type_attrib in g.attrib and not kvg_element_attrib in g.attrib:
        return [find_all_element(child) for child in g]

    return [g.get(kvg_element_attrib), [find_all_element(child) for child in g]]


def find_element_children(g):
    kanji = g.get(kvg_element_attrib)

    elem = []
    for child in g:
        if kvg_element_attrib in child.attrib:
            elem.append(child.get(kvg_element_attrib))
        else:
            for c in child:
                if kvg_element_attrib in c.attrib:
                    elem.append(c.get(kvg_element_attrib))

    return [kanji, elem]


def find_element_top_buttom(g):
    kanji = g.get(kvg_element_attrib)

    elem = []
    if len(g) == 2:
        g0_position = g[0].get(kvg_position_attrib)
        g1_position = g[1].get(kvg_position_attrib)
        if g0_position == "top" and g1_position == "bottom":
            elem = [child.get(kvg_element_attrib) for child in g]

    if elem:
        return [kanji, elem]
    else:
        return []


def find_element_left_right(g):
    kanji = g.get(kvg_element_attrib)

    elem = []
    if len(g) == 2:
        g0_position = g[0].get(kvg_position_attrib)
        g1_position = g[1].get(kvg_position_attrib)
        if g0_position == "left" and g1_position == "right":
            elem = [child.get(kvg_element_attrib) for child in g]

    if elem:
        return [kanji, elem]
    else:
        return []


def convert_dict(pairs):
    kanji2radical = {}
    radical2kanji = defaultdict(list)
    for pair in pairs:
        kanji2radical[pair[0]] = pair[1]
        for radical in pair[1]:
            radical2kanji[radical].append(pair[0])
    return kanji2radical, radical2kanji


def to_json(d, filename):
    with open(filename, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=4, sort_keys=True)


def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


if __name__ == '__main__':
    kanji_list = []
    pair_element = []
    pair_children = []
    pair_top_buttom = []
    pair_left_right = []

    for svg in Path("kanji/").glob("*.svg"):
        tree = ElementTree.parse(svg)
        root = tree.getroot()
        stroke_paths = root[0][0]

        kanji = stroke_paths.get(kvg_element_attrib)

        # すべてのelementを抽出
        p_list_all = list(flatten(find_all_element(stroke_paths)))
        p_list = [c for c in p_list_all if c != ""]
        if len(p_list) >= 2:
            pair_element.append([p_list[0], list(set(p_list[1:]))])
            kanji_list.append([svg.stem, kanji, unicodedata.name(kanji, "UNKNOWN")])

        # root直下のelementだけを抽出
        pair = find_element_children(stroke_paths)
        if pair[0] and pair[1]:
            pair_children.append(pair)

        # 上下に分かれる漢字だけを抽出
        top_buttom = find_element_top_buttom(stroke_paths)
        if top_buttom and all(v is not None for v in top_buttom[1]):
            pair_top_buttom.append(top_buttom)

        # 左右に分かれる漢字だけを抽出
        left_right = find_element_left_right(stroke_paths)
        if left_right and all(v is not None for v in left_right[1]):
            pair_left_right.append(left_right)

    with open("data/kanji.txt", "w") as f:
        for l in kanji_list:
            f.write("\t".join(l) + "\n")

    kanji2element, element2kanji = convert_dict(pair_element)
    to_json(kanji2element, "data/kanji2element.json")
    to_json(element2kanji, "data/element2kanji.json")

    kanji2radical, radical2kanji = convert_dict(pair_children)
    to_json(kanji2radical, "data/kanji2radical.json")
    to_json(radical2kanji, "data/radical2kanji.json")

    kanji2radical_top_buttom, radical2kanji_top_buttom = convert_dict(pair_top_buttom)
    to_json(kanji2radical_top_buttom, "data/kanji2radical_top_buttom.json")
    to_json(radical2kanji_top_buttom, "data/radical2kanji_top_buttom.json")

    kanji2radical_left_right, radical2kanji_left_right = convert_dict(pair_left_right)
    to_json(kanji2radical_left_right, "data/kanji2radical_left_right.json")
    to_json(radical2kanji_left_right, "data/radical2kanji_left_right.json")
