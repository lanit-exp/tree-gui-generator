__all__ = ["generate_trees", "generate_trees"]

import argparse
import sys
from collections import namedtuple
from pathlib import Path
from random import choices, randrange
from typing import List, Dict, Set, Tuple, Optional

from tree_gui_generator.fileproc import FileProc, PROJ_ROOT_DIR
from tree_gui_generator.model import ContWidget, Node, \
    CompWidgetContent, Tree, Descriptions, DTOMapper

DESCR_DIR_PATH = PROJ_ROOT_DIR / "resources/configs/cut_configs/__current__almost_ok"
OTP_PATH = PROJ_ROOT_DIR / "resources/generated_trees"

WidgetInfo = namedtuple("WidgetInfo", ["prob", "solo"])
NodeInfo = namedtuple("NodeInfo", ["node", "type"])


# building tree --------------------------------------------------------------------------------------------------------
def generate_tree(nwidgets: int, descrs: Descriptions) -> Tuple[Tree, List[Node]]:
    nodes = sample(descrs.tree.root, nwidgets, descrs)
    tree = build_tree(nodes, descrs)
    return tree, nodes


def build_tree(sample: List[Node], descrs: Descriptions):
    container_subtrees: List[Node] = get_cont_subtrees(sample, descrs)
    while len(container_subtrees) > 1:
        link_two_rand_container_subtrees(container_subtrees, descrs)

    root_node: Node = container_subtrees[0]

    cont_tree_nodes: List[Node] = [node for node in sample if node.name in descrs.cont.keys()]
    comp_tree_nodes: List[Node] = [node for node in sample if node.name in descrs.comp.keys()]
    for comp_node in comp_tree_nodes:
        cont_tree_nodes += get_all_comp_containers(comp_node, descrs)

    not_cont_tree_nodes: List[Node] = [node for node in sample
                                       if node.name in descrs.atomic.keys()]
    for comp_node in comp_tree_nodes:
        if not has_container_as_child(comp_node, descrs):
            not_cont_tree_nodes.append(comp_node)

    while len(not_cont_tree_nodes) > 0:
        link_to_rand_container_node(cont_tree_nodes, not_cont_tree_nodes, descrs)

    remove_empty_containers(root_node, descrs)
    return Tree(root_node)


def get_cont_subtrees(nodes: List[Node], descrs: Descriptions) -> List[
    Node]:
    result = []
    for node in nodes:
        if node.name in descrs.comp.keys() and has_container_as_child(node, descrs):
            result.append(node)
        elif node.name in descrs.cont.keys() and node.parent is None:
            result.append(node)
    return result


def has_container_as_child(node: 'Node', descrs: Descriptions) -> bool:
    def find_cont(node_: 'Node'):
        for child in node_.children:
            if child.name in descrs.cont.keys():
                return True
            elif child.name in descrs.comp.keys():
                find_cont(child)
        return False

    return find_cont(node)


def link_two_rand_container_subtrees(cont_subtrees: List['Node'], descrs: Descriptions):
    parent_index: int = randrange(0, len(cont_subtrees))
    child_index: int = randrange(0, len(cont_subtrees))
    if parent_index != child_index:
        parent_node = cont_subtrees[parent_index]
        child_node = cont_subtrees[child_index]

        if can_be_parent_child(parent_node, child_node, descrs):
            adding_result, cont_parent_node = add_child(parent_node, child_node, descrs)
            link_only_children(child_node, cont_subtrees, descrs)
            cont_subtrees.remove(child_node)

            if cont_parent_node is not None:
                excess_children_count = len(cont_parent_node.children) \
                                        - descrs.cont[cont_parent_node.name].max_nwidget
                if excess_children_count >= 0 and parent_index != 0:
                    cont_subtrees.pop(parent_index)
                while excess_children_count > 0:
                    node_to_remove_index = randrange(0, len(parent_node.children))
                    parent_node.children.pop(node_to_remove_index)
                    excess_children_count -= 1


def add_child(parent: 'Node', child: 'Node', descrs: Descriptions) \
        -> Tuple[bool, Optional['Node']]:
    def find_potent_parents(parent_: 'Node', pot_parents: List['Node']):
        if parent_.name in descrs.cont.keys() and child.name in descrs.cont[parent_.name].children:
            pot_parents.append(parent_)
        elif parent_.name in descrs.comp.keys():
            for comps_child in parent_.children:
                if comps_child.name in descrs.comp:
                    find_potent_parents(comps_child, pot_parents)
                elif comps_child.name in descrs.cont:
                    if child.name in descrs.cont[comps_child.name].children:
                        pot_parents.append(comps_child)

    potent_parents = []
    find_potent_parents(parent, potent_parents)
    if potent_parents:
        chosen_parent = choices(potent_parents, k=1)[0]
        chosen_parent.children.append(child)
        child.parent = chosen_parent
        return True, chosen_parent
    else:
        return False, None


def can_be_parent_child(parent: 'Node', child: 'Node', descrs: Descriptions):
    if child.name == descrs.tree.root:
        return False
    if parent.name in descrs.cont.keys() \
            and child.name in descrs.cont[parent.name].children \
            and len(parent.children) < descrs.cont[parent.name].max_nwidget:
        return True
    if parent.name in descrs.comp.keys():
        ok = False
        for possible_container in parent.children:
            ok = can_be_parent_child(possible_container, child, descrs)
            if ok:
                break
        return ok
    return False


def link_only_children(node: Node, cont_subtrees: List['Node'], descrs: Descriptions):
    if node.name in descrs.cont.keys():
        link_only_cont_children(node, cont_subtrees, descrs.cont)
    elif node.name in descrs.comp.keys():
        comp_containers = get_all_comp_containers(node, descrs)
        for comp_cont_node in comp_containers:
            link_only_cont_children(comp_cont_node, cont_subtrees, descrs.cont)


def link_only_cont_children(target_node: Node, cont_subtrees: List['Node'], cont_map: Dict[str, ContWidget]):
    target_node_childrens_parent_count = {child.name: 0 for child in cont_subtrees if
                                          child.name in target_node.children}
    for cont_or_comp_node in cont_subtrees:
        if cont_or_comp_node.name in cont_map.keys():
            cont_node = cont_or_comp_node
            for cont_node_child_name in cont_map[cont_node.name].children:
                if cont_node_child_name in target_node_childrens_parent_count.keys():
                    target_node_childrens_parent_count[cont_node_child_name] += 1
    for child in target_node.children:
        if child.name in target_node_childrens_parent_count.keys() \
                and target_node_childrens_parent_count[child.name] < 2:
            target_node.add_child(child)
            cont_subtrees.remove(child)


def get_all_comp_containers(node: 'Node', descrs: Descriptions) -> List[Node]:
    def find_cont(node_: 'Node'):
        for child in node_.children:
            if child.name in descrs.cont.keys():
                res.append(child)
            elif child.name in descrs.comp.keys():
                find_cont(child)

    res = []
    find_cont(node)
    return res


def link_to_rand_container_node(cont_tree_nodes: List[Node], atomic_tree_nodes: List[Node],
                                descrs: Descriptions):
    parent_index: int = randrange(0, len(cont_tree_nodes))
    child_index: int = randrange(0, len(atomic_tree_nodes))

    child = atomic_tree_nodes[child_index]
    parent = cont_tree_nodes[parent_index]

    if can_be_parent_child(parent, child, descrs):
        adding_result, cont_parent_node = add_child(parent, child, descrs)
        atomic_tree_nodes.pop(child_index)

        if cont_parent_node is not None:
            excess_children_count = len(cont_parent_node.children) \
                                    - descrs.cont[cont_parent_node.name].max_nwidget
            if excess_children_count >= 0:
                cont_tree_nodes.pop(parent_index)
            while excess_children_count > 0:
                node_to_remove_index = randrange(0, len(parent.children))
                parent.children.pop(node_to_remove_index)
                excess_children_count -= 1


def remove_empty_containers(tree: 'Node', descrs: Descriptions):
    def traversal(node: Node):
        node_child_index = 0
        while node_child_index < len(node.children):
            node_child = node.children[node_child_index]
            if node_child in descrs.cont or node_child in descrs.comp:
                traversal(node_child)
            if node_child in descrs.cont and not node_child.children:
                node.children.pop(node_child_index)
                node_child_index -= 1
            node_child_index += 1

    traversal(tree)


# create sample --------------------------------------------------------------------------------------------------------
def sample(root_name: str, nwidgets: int, descrs: Descriptions) -> List[Node]:
    general_domain: Dict[str, WidgetInfo] = {name: WidgetInfo(w.prob, w.solo)
                                             for name, w in descrs.atomic.items()}
    general_domain.update({name: WidgetInfo(w.prob, w.solo)
                           for name, w in descrs.comp.items()})
    general_domain.update({name: WidgetInfo(w.prob, w.solo)
                           for name, w in descrs.cont.items()})

    current_domain: Dict[str, WidgetInfo] = {root_name: general_domain[root_name]}
    sampled_widget: Set[str] = {root_name}

    root_node = Node(root_name)
    if root_name in descrs.comp.keys():
        root_node = create_comp_node(root_name, descrs)
    update_domain(current_domain, general_domain, root_node, descrs)

    if current_domain[root_name].solo and root_name in sampled_widget:
        del current_domain[root_name]

    if not current_domain.keys():
        raise RuntimeError("Wrong widget hierarchy")

    sample: List[Node] = [root_node]
    while (len(sample) < nwidgets):
        probs = [w_info.prob for w_info in current_domain.values()]
        widget_name = choices(list(current_domain.keys()), weights=probs, k=1)[0]
        sampled_widget.add(widget_name)
        if widget_name in descrs.comp.keys():
            widget_node = create_comp_node(widget_name, descrs)
            update_domain(current_domain, general_domain, widget_node, descrs)
        else:
            widget_node = create_node(widget_name)
            if widget_name in descrs.cont.keys():
                current_domain.update(
                    {child_name: general_domain[child_name] for child_name in descrs.cont[widget_name].children})

        if current_domain[widget_name].solo and widget_name in sampled_widget:
            del current_domain[widget_name]

        sample.append(widget_node)

    return sample


def update_domain(current_domain: Dict[str, WidgetInfo], general_domain: Dict[str, WidgetInfo], added_node: Node,
                  descrs: Descriptions):
    if added_node.name in descrs.comp.keys():
        for child in added_node.children:
            if child.name in descrs.cont.keys():
                cont = child
                current_domain.update(
                    {cont_child: general_domain[cont_child]
                     for cont_child in descrs.cont[cont.name].children})
    elif added_node.name in descrs.cont.keys():
        current_domain.update({child_name: general_domain[child_name]
                               for child_name in descrs.cont[added_node.name].children})


def create_comp_node(comp_name: str, descrs: Descriptions) -> Node:
    comp_widget = descrs.comp[comp_name]
    content_items: List[CompWidgetContent] = comp_widget.content

    by_group = {cont_item.group: [] for cont_item in content_items}
    for cont_item in content_items:
        by_group[cont_item.group].append(cont_item)

    children: List[Node] = []
    for group, cont_items in by_group.items():
        content_name = gen_comp_node_content(cont_items)
        if content_name in descrs.comp.keys():
            content_node \
                = create_comp_node(content_name, descrs)
        else:
            content_node = create_node(content_name)
        children.append(content_node)

    comp_node = Node(comp_widget.name, children=children)
    for child in children:
        child.parent = comp_node
    return comp_node


def create_node(widget_name):
    return Node(widget_name)


def gen_comp_node_content(cont_items: List[CompWidgetContent]):
    probs = [content.prob for content in cont_items]
    names = [content.name for content in cont_items]
    child_name = choices(names, weights=probs, k=1)[0]
    return child_name


# main -----------------------------------------------------------------------------------------------------
def generate_trees(ntrees: int, otp_path: Path, descrs: Descriptions):
    for itree in range(ntrees):
        nwidgets = randrange(descrs.tree.min_nwidgets, descrs.tree.max_nwidgets)
        tree, nodes = generate_tree(nwidgets, descrs)
        print_info(tree, nodes)

        tree_dto = DTOMapper.map_tree_dto(tree)
        FileProc.write_json(tree_dto, otp_path / f"tree{itree + 1}.json")


def print_info(tree: Tree, nodes: List['Node']):
    print(tree, f"\n\n<------ Nodes ------> n_nodes: {len(nodes)}")
    for node in nodes:
        print(node)
    print('<------ Nodes ------>')


def __parse_args(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__)

    parser.add_argument("ntrees", type=int, help="number of tree to generate")
    parser.add_argument("--conf", type=str, default=str(DESCR_DIR_PATH),
                        help="config directory path")
    parser.add_argument("--otp", type=str, default=str(OTP_PATH),
                        help="directory where generated trees are placed")

    return parser.parse_args(args)

def main():
    options = __parse_args()
    descr = Descriptions(Path(options.conf))
    otp = Path(options.otp)

    ntrees = options.ntrees
    generate_trees(ntrees, otp, descr)
