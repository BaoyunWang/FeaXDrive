"""Check source/config links without importing GPU or NAVSIM dependencies.

Run from the repository root: python -m unittest discover -s tests -v
These checks detect dangling references after file cleanup; they do not replace
runtime training or evaluation with real assets.
"""

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return path.read_text(encoding="utf-8-sig")


def module_exists(module):
    path = ROOT.joinpath(*module.split("."))
    return path.with_suffix(".py").is_file() or path.is_dir()


class RepositoryStructureTests(unittest.TestCase):
    def test_navsim_imports_resolve(self):
        for path in sorted((ROOT / "navsim").rglob("*.py")):
            relative = path.relative_to(ROOT)
            package = list(relative.parent.parts)
            tree = ast.parse(read(path), filename=str(relative))
            for node in ast.walk(tree):
                modules = []
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        parts = package[:len(package) - node.level + 1]
                        if node.module:
                            parts += node.module.split(".")
                        modules = [".".join(parts)]
                    elif node.module:
                        modules = [node.module]
                for module in modules:
                    if module == "navsim" or module.startswith("navsim."):
                        with self.subTest(file=str(relative), line=node.lineno):
                            self.assertTrue(module_exists(module), module)

    def test_hydra_targets_exist(self):
        target_pattern = re.compile(r"^\s*_target_:\s*(navsim\.[\w.]+)", re.M)
        for path in sorted((ROOT / "navsim").rglob("*.yaml")):
            for target in target_pattern.findall(read(path)):
                module, symbol = target.rsplit(".", 1)
                with self.subTest(file=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue(module_exists(module), module)
                    module_path = ROOT.joinpath(*module.split(".")).with_suffix(".py")
                    tree = ast.parse(read(module_path))
                    names = {
                        node.name for node in tree.body
                        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                    }
                    for node in tree.body:
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            names.update(alias.asname or alias.name for alias in node.names)
                        elif isinstance(node, ast.Assign):
                            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
                    self.assertIn(symbol, names)

    def test_literal_agent_configs_exist(self):
        pattern = re.compile(r"(?:\bagent=|^\s*-\s+agent:\s*)([a-z][a-z0-9_]*_agent)\b", re.M)
        paths = list((ROOT / "scripts").rglob("*.sh"))
        paths += list((ROOT / "scripts").rglob("*.slurm"))
        paths += list((ROOT / "navsim/planning/script/config").rglob("*.yaml"))
        for path in sorted(paths):
            for name in pattern.findall(read(path)):
                with self.subTest(file=str(path.relative_to(ROOT)), agent=name):
                    self.assertTrue((ROOT / "navsim/planning/script/config/common/agent" / (name + ".yaml")).is_file())

    def test_shell_python_paths_exist(self):
        pattern = re.compile(r"\bnavsim/[\w/]+\.py\b")
        paths = list((ROOT / "scripts").rglob("*.sh"))
        paths += list((ROOT / "scripts").rglob("*.slurm"))
        for path in sorted(paths):
            for target in pattern.findall(read(path)):
                with self.subTest(file=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue((ROOT / target).is_file())


if __name__ == "__main__":
    unittest.main()
