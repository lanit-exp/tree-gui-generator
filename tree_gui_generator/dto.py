from typing import List


class BaseWidgetDTO:
    def __init__(self, name: str, style: List[str] = None):
        if style is None:
            style = []

        self.name = name
        self.style = style


class AtomicWidgetDTO(BaseWidgetDTO):
    def __init__(self, name: str, solo: bool = False, prob: float = 0, style: List[str] = None):
        super().__init__(name, style)

        self.solo = solo
        self.prob = prob


class CompWidgetDTO(AtomicWidgetDTO):
    def __init__(self, name: str, solo: bool = False, prob: float = 0, nrows: int = 1, ncols: int = 1,
                 style: List[str] = None, content: List['CompWidgetContentDTO'] = None):
        super().__init__(name, solo, prob, style)
        if content is None:
            content = []

        self.nrows = nrows
        self.ncols = ncols
        self.content = content


class CompWidgetContentDTO(BaseWidgetDTO):
    def __init__(self, name: str, group: int, row: int, col: int, row_span: int = 0, col_span: int = 0, prob: float = 1,
                 style: List[str] = None):
        super().__init__(name)
        if style is None:
            style = []

        self.group = group
        self.row = row
        self.col = col
        self.row_span = row_span
        self.col_span = col_span
        self.prob = prob
        self.style = style


class ContWidgetDTO(AtomicWidgetDTO):
    def __init__(self, name: str, direction: str, children: List[str], solo: bool = False, prob: float = 0,
                 nrows: int = 0, ncols: int = 0, style: List[str] = None):
        super().__init__(name, solo, prob, style)
        self.direction = direction
        self.children = children
        self.nrows = nrows
        self.ncols = ncols


class TreeDescrDTO(object):
    def __init__(self, root: str, min_nwidgets: int, max_nwidgets: int):
        self.root = root
        self.min_nwidgets = min_nwidgets
        self.max_nwidgets = max_nwidgets


class RangeDTO(object):
    def __init__(self, max_val: int, min_val: int):
        self.max_val = max_val
        self.min_val = min_val


class NodeDTO(object):
    def __init__(self, name: str, children=None):
        if children is None:
            children = []
        self.name: str = name
        self.children: List['NodeDTO'] = children


class TreeDTO(object):
    def __init__(self, root: 'NodeDTO'):
        self.root = root
