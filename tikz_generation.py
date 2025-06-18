import os
import re
import json
import subprocess
from pathlib import Path
from collections import defaultdict, deque

M2_DIR = Path("ICERM_Computation/rooted_level-1_networks")
OUTPUT_DIR = Path("webpage/data")
TEMP_DIR = Path("temp_compile")

def parse_edge_list(line):
    matches = re.findall(r'\{("?[^\{\},"]+"?),("?[^\{\},"]+"?)\}', line)
    edges = [(int(u) if u.lstrip('-').isdigit() else u.strip('"'),
          int(v) if v.lstrip('-').isdigit() else v.strip('"'))
         for u, v in matches]
    return edges

def make_tikz(edges, root=None):
    children = defaultdict(list)
    parents = defaultdict(list)
    nodes = set()
    for u, v in edges:
        children[u].append(v)
        parents[v].append(u)
        nodes.update([u, v])

    if root is None:
        candidates = nodes - set(parents.keys())
        if len(candidates) != 1:
            raise ValueError("Root is ambiguous; please specify one.")
        root = list(candidates)[0]

    layers = defaultdict(list)
    level = {root: 0}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        depth = level[node]
        layers[depth].append(node)
        for child in children[node]:
            if child not in level:
                level[child] = depth + 1
                queue.append(child)

    tikz_lines = [
        "\\documentclass[border=2pt]{standalone}",
        "\\usepackage{tikz}",
        "\\usetikzlibrary{graphs, graphdrawing}",
        "\\usegdlibrary{layered}",
        "\\begin{document}",
        "\\begin{tikzpicture}[>=stealth]",
        "\\graph [layered layout, sibling distance=15mm] {"
    ]

    for u, v in edges:
        tikz_lines.append(f'  "{u}" -> "{v}";')

    tikz_lines.append("};")
    tikz_lines.append("\\end{tikzpicture}")
    tikz_lines.append("\\end{document}")

    return "\n".join(tikz_lines)

# def compile_svg(latex_str, svg_path, tmp_dir):
#     tex_path = tmp_dir / "graph.tex"
#     pdf_path = tmp_dir / "graph.pdf"
#     svg_tmp_path = tmp_dir / "graph.svg"
#     with open(tex_path, "w") as f:
#         f.write(latex_str)

#     subprocess.run(["lualatex", "-interaction=nonstopmode", tex_path.name],
#                    cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#     subprocess.run(["pdf2svg", "graph.pdf", str(svg_path)],
#                    cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
#     svg_tmp_path.rename(svg_path)

def compile_svg(latex_str, svg_dest, tmp_dir):
    tex_path = tmp_dir / "graph.tex"
    pdf_path = tmp_dir / "graph.pdf"
    svg_tmp_path = tmp_dir / "graph.svg"

    with open(tex_path, "w") as f:
        f.write(latex_str)

    # Compile LaTeX to PDF
    subprocess.run(["lualatex", "-interaction=nonstopmode", tex_path.name],
                   cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not pdf_path.exists():
        raise RuntimeError("❌ PDF not generated. LaTeX compilation failed.")

    # Convert PDF to SVG
    result = subprocess.run(["pdf2svg", "graph.pdf", "graph.svg"],
                            cwd=tmp_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not svg_tmp_path.exists():
        raise RuntimeError(f"❌ SVG not generated. pdf2svg failed.\n"
                           f"stderr: {result.stderr.decode().strip()}")

    svg_tmp_path.rename(svg_dest)



def process_class_file(filepath, class_name):
    output_folder = OUTPUT_DIR / class_name
    output_folder.mkdir(parents=True, exist_ok=True)

    TEMP_DIR.mkdir(exist_ok=True)
    graph_files = []

    with open(filepath) as f:
        for i, line in enumerate(f):
            line = line.strip().rstrip(";")
            if not line or line.startswith("--"):
                continue
            try:
                edges = parse_edge_list(line)
                latex_str = make_tikz(edges, root=-1)
                svg_filename = f"graph{i:04}.svg"
                svg_path = output_folder / svg_filename
                compile_svg(latex_str, svg_path, TEMP_DIR)
                graph_files.append(svg_filename)
                print(f"  → graph{i:04} processed")
            except Exception as e:
                print(f"Error in {class_name}, line {i}: {e}")

    with open(OUTPUT_DIR / f"{class_name}.json", "w") as f:
        json.dump({"class": class_name, "graphs": graph_files}, f, indent=2)

    # Cleanup temp
    for ext in [".aux", ".log", ".pdf", ".tex"]:
        try:
            os.remove(TEMP_DIR / f"graph{ext}")
        except FileNotFoundError:
            pass

def main():
    # E = [(-1,0),(-1,8),(0,1),(0,"B"),(8,1),(8,7),(1,"C"),(7,6),(7,2),(6,5),(6,2),(5,4),(5,3),(2,"D"),(4,"A"),(4,3),(3,"E")]
    # print(make_tikz(E, root = -1))
    
    for m2_file in M2_DIR.glob("*.m2"):
        class_name = m2_file.stem
        print(f"Processing {class_name}...")
        process_class_file(m2_file, class_name)

if __name__ == "__main__":
    main()
