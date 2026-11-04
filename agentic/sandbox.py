from pathlib import Path
def list_source_files(path): return sorted(str(p) for p in Path(path).rglob('*.py'))
