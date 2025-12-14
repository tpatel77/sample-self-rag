
import pkgutil
import inspect
import importlib
import google.adk

def search_term_in_package(package, term):
    path = package.__path__
    prefix = package.__name__ + "."
    found = False
    
    for _, name, ispkg in pkgutil.walk_packages(path, prefix):
        try:
            module = importlib.import_module(name)
            # Check module name
            if term.lower() in name.lower():
                 print(f"FOUND in module name: {name}")
                 found = True
            
            # Check class names
            for member_name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and term.lower() in member_name.lower():
                     print(f"FOUND class: {member_name} in {name}")
                     found = True
        except Exception:
            continue
            
    if not found:
        print(f"Term '{term}' not found in package {package.__name__}")

print("Searching for 'Redis' in google.adk...")
search_term_in_package(google.adk, "Redis")
