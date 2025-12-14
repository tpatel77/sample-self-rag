
import inspect
from google.adk.agents import LoopAgent

print("Docstring for LoopAgent:")
print(LoopAgent.__doc__)

print("\nInit signature:")
print(inspect.signature(LoopAgent.__init__))

# If we can, lets inspect source of _run_async_impl if possible (might not work for compiled or restricted libs)
try:
    print("\nSource of _run_async_impl:")
    print(inspect.getsource(LoopAgent._run_async_impl))
except Exception as e:
    print(f"\nCould not get source: {e}")
