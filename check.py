import ast, importlib.util
from pathlib import Path
def main():
    root=Path(__file__).parent
    py=list(root.rglob("*.py"))
    for p in py: ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    for p in py:
        if p.name=="__init__.py": continue
        rel=p.relative_to(root).with_suffix("")
        mod=".".join(rel.parts)
        importlib.util.find_spec(mod)
    print(f"Syntax/import discovery OK: {len(py)} Python files")
if __name__=="__main__": main()
