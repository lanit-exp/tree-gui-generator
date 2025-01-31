__all__ = ["FileProc"]

from json import dumps, load
from os.path import dirname, abspath
from pathlib import Path
from typing import Dict, Callable, Any

SRC_ROOT_DIR: Path = Path(dirname(abspath(__file__)))
PROJ_ROOT_DIR: Path = Path(SRC_ROOT_DIR).parent


class FileProc(object):
    @classmethod
    def write_json(cls, obj, p: Path, mode: str = 'w', mk_parents: bool = True, exist_ok: bool = True,
                   obj_hook: Callable[[Any], Dict] = None):
        if obj_hook is None:
            obj_hook = lambda d: d.__dict__

        filepath = p.parent
        if filepath:
            filepath.mkdir(parents=mk_parents, exist_ok=exist_ok)
        with open(p, mode) as out:
            json_str = dumps(obj, default=obj_hook)
            out.write(json_str)

    @classmethod
    def read_json(cls, p: Path, obj_hook: Callable[[Dict], Any] = None, mode: str = 'r') -> Any:
        with open(p, mode) as fin:
            data = load(fin, object_hook=obj_hook)
        return data

    @classmethod
    def write_file(cls, p: Path, text: str, mode: str = 'w', mk_parents: bool = True, exist_ok: bool = True):
        dir_path = p.parent
        dir_path.mkdir(parents=mk_parents, exist_ok=exist_ok)
        with open(p, mode) as out:
            out.write(text)
