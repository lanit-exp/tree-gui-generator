__all__ = ['Descriptions']
from pathlib import Path
from typing import List, Dict, Tuple

from tree_gui_generator.dto import CompWidgetDTO, CompWidgetContentDTO, AtomicWidgetDTO, ContWidgetDTO, TreeDescrDTO, \
    TreeDTO, NodeDTO
from tree_gui_generator.fileproc import FileProc


class TreeDescr(object):
    def __init__(self, root: str, min_nwidgets: int, max_nwidgets: int):
        self._root = root
        self._min_nwidgets = min_nwidgets
        self._max_nwidgets = max_nwidgets

    @property
    def root(self) -> str:
        return self._root

    @property
    def min_nwidgets(self) -> int:
        return self._min_nwidgets

    @property
    def max_nwidgets(self) -> int:
        return self._max_nwidgets

    def __repr__(self):
        return f"<TreeDescr -- root: {self._root}, min_nwidgets: {self._min_nwidgets}, " \
               f"max_nwidgets: {self._max_nwidgets}>"

class AtomicWidget(object):
    def __init__(self, name: str, solo: bool, prob: float):
        self._name = name
        self._solo = solo
        self._prob = prob

    @property
    def name(self):
        return self._name

    @property
    def solo(self) -> bool:
        return self._solo

    @property
    def prob(self) -> float:
        return self._prob

    def _props_repr(self) -> str:
        return f"name: {self._name}, solo: {self._solo}, prob: {self._prob}"

    def __repr__(self):
        return f"<AtomicWidget -- {self._props_repr()}>"


class CompWidget(AtomicWidget):
    def __init__(self, name: str, solo: bool, prob: float, content: List['CompWidgetContent']):
        super().__init__(name, solo, prob)
        if content is None:
            content = []

        self._content = content

    @property
    def content(self) -> List['CompWidgetContent']:
        return self._content

    def _props_repr(self) -> str:
        return f"{super()._props_repr()}, content: {self._content}"

    def __repr__(self):
        return f"<CompWidget -- {self._props_repr()}"


class CompWidgetContent(object):
    def __init__(self, name: str, group: int, prob: float):
        self._name = name
        self._group = group
        self._prob = prob

    @property
    def name(self):
        return self._name

    @property
    def group(self) -> int:
        return self._group

    @property
    def prob(self):
        return self._prob

    def _props_repr(self) -> str:
        return f"name: {self._name}, group: {self._group}, prob: {self._prob}"

    def __repr__(self):
        return f"<CompWidgetContent -- {self._props_repr()}>"


class ContWidget(AtomicWidget):
    def __init__(self, name: str, children: List[str], solo: bool, prob: float, max_nwidget: int):
        super().__init__(name, solo, prob)
        self._children = children
        self._max_nwidgets = max_nwidget if max_nwidget > 0 else 1_000_000

    @property
    def children(self):
        return self._children

    @property
    def max_nwidget(self):
        return self._max_nwidgets

    def _props_repr(self) -> str:
        return f"{super()._props_repr()}, children: {self._children}"

    def __repr__(self):
        return f"<ContWidget -- {self._props_repr()}"


class Tree(object):
    def __init__(self, root: 'Node'):
        self._root = root

    @property
    def root(self) -> 'Node':
        return self._root

    def __repr__(self):
        def dfs(node: Node, level: int) -> None:
            result_string_list.append(("    " * level)
                                      + f"<level {level}>::{node.__str__()}"
                                      + f"::<amount of children {len(node.children)}>")
            for child_node in node.children:
                dfs(child_node, level + 1)

        obj_marker = f"<------ Tree ------>"
        result_string_list = [obj_marker]
        dfs(self.root, 0)
        result_string_list.append(obj_marker + f" nwidget: {len(result_string_list) - 1}")
        return '\n'.join(result_string_list)


class Node(object):
    def __init__(self, name: str, parent: 'Node' = None, children: List['Node'] = None):
        if children is None:
            children = []

        self._name = name
        self._children = children
        self._parent = parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def children(self) -> List['Node']:
        return self._children

    @property
    def parent(self) -> 'Node':
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    def add_children(self, children: List['Node']):
        self._children.extend(children)

    def add_child(self, child: 'Node'):
        self._children.append(child)

    def can_have_as_child(self, potential_child: 'Node', containers: Dict[str, ContWidget]) -> bool:
        return (self._name in containers.keys()) and (potential_child.name in containers[self._name].children)

    def get_node_and_descendants(self) -> List['Node']:
        def dfs(ls: List['Node'], node: 'Node'):
            ls.append(node)
            for child in node.children:
                dfs(ls, child)

        result = []
        dfs(result, self)
        return result

    def __repr__(self):
        return f'<Node -- name: {self._name} children: {self._children}>'

    def __str__(self):
        return f'<Node -- name: {self._name}>'


class Descriptions(object):
    def __init__(self, path):
        atomic_list, comp_list, cont_list, self.tree \
            = Reader.read_descriptions(path)
        self.atomic = {item.name: item for item in atomic_list}
        self.comp = {item.name: item for item in comp_list}
        self.cont = {item.name: item for item in cont_list}


class DTOMapper(object):
    @classmethod
    def map_atomic_widget(cls, dto: AtomicWidgetDTO) -> AtomicWidget:
        return AtomicWidget(dto.name, dto.solo, dto.prob)

    @classmethod
    def map_comp_widget(cls, dto: CompWidgetDTO) -> CompWidget:
        content = []
        for cont_item_dto in dto.content:
            content.append(cls.map_comp_widget_content(cont_item_dto))

        return CompWidget(dto.name, dto.solo, dto.prob, content)

    @classmethod
    def map_comp_widget_content(cls, dto: CompWidgetContentDTO) -> CompWidgetContent:
        return CompWidgetContent(dto.name, dto.group, dto.prob)

    @classmethod
    def map_cont_widget(cls, dto: ContWidgetDTO) -> ContWidget:
        max_nwidgets = dto.ncols * dto.nrows
        return ContWidget(dto.name, dto.children, dto.solo, dto.prob, max_nwidgets)

    @classmethod
    def map_tree_descr(cls, dto: TreeDescrDTO) -> TreeDescr:
        return TreeDescr(dto.root, dto.min_nwidgets, dto.max_nwidgets)

    @classmethod
    def map_tree_dto(cls, tree: Tree) -> TreeDTO:
        def dfs(node: 'Node') -> NodeDTO:
            node_dto = NodeDTO(node.name)
            for child in node.children:
                child_dto = dfs(child)
                node_dto.children.append(child_dto)
            return node_dto

        root_dto = dfs(tree.root)
        return TreeDTO(root_dto)


class Reader(object):
    _ATOMIC = Path("atomic_widget_descr.json")
    _COMPOSITE = Path("comp_widget_descr.json")
    _CONTAINER = Path("cont_widget_descr.json")
    _TREE_DESCR = Path("tree_descr.json")

    @classmethod
    def __comp_list_json_reader_hook(cls, d: Dict):
        try:
            return CompWidgetDTO(**d)
        except:
            return CompWidgetContentDTO(**d)

    @classmethod
    def read_descriptions(cls, dir_path: Path) \
            -> Tuple[List[AtomicWidget], List[CompWidget], List[ContWidget], TreeDescr]:
        atomic_list_dto: List[AtomicWidgetDTO] = FileProc.read_json(dir_path / cls._ATOMIC,
                                                                    obj_hook=lambda d: AtomicWidgetDTO(**d))
        comp_list_dto: List[CompWidgetDTO] = FileProc.read_json(dir_path / cls._COMPOSITE,
                                                                obj_hook=lambda d: cls.__comp_list_json_reader_hook(d))
        cont_list_dto: List[ContWidgetDTO] = FileProc.read_json(dir_path / cls._CONTAINER,
                                                                obj_hook=lambda d: ContWidgetDTO(**d))
        tree_descr_dto: TreeDescrDTO = FileProc.read_json(dir_path / cls._TREE_DESCR,
                                                          obj_hook=lambda d: TreeDescrDTO(**d))

        atomic_list = [DTOMapper.map_atomic_widget(item) for item in atomic_list_dto]
        comp_list = [DTOMapper.map_comp_widget(item) for item in comp_list_dto]
        cont_list = [DTOMapper.map_cont_widget(item) for item in cont_list_dto]
        tree_descr = DTOMapper.map_tree_descr(tree_descr_dto)
        return atomic_list, comp_list, cont_list, tree_descr


class Writer(object):
    @classmethod
    def write_tree(cls, file_path: Path, tree: Node):
        FileProc.write_json(tree, file_path)
