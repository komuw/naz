import os
import ast


here = os.path.abspath(os.path.dirname("naz"))
about = {}
with open(os.path.join(here, "naz", "__version__.py"), "r") as f:
    x = f.read()
    y = x.replace("about = ", "")
    about = ast.literal_eval(y)

print(about["__version__"])
