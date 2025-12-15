import copy
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from typing import List, Dict, Tuple

# =========================================
# Petri Network class
# =========================================
class PetriNetwork:
    """
    Represents a Petri net with places, transitions, and initial marking.
    Handles enabling of transitions and firing them.
    """
    def __init__(self, places: List[str], transitions: Dict[str, Dict], initial_marking: List[int]):
        self.places = places                  # List of place names
        self.transitions = transitions        # Dictionary of transitions {name: {'in':{}, 'out':{}}}
        self.initial_marking = initial_marking  # Initial marking of places

    def is_enabled(self, transition: str, marking: List[int]) -> bool:
        """
        Check if a transition can be fired given the current marking.
        """
        if transition not in self.transitions:
            return False
        for place, weight in self.transitions[transition]['in'].items():
            idx = self.places.index(place)
            if marking[idx] < weight:  # Not enough tokens
                return False
        return True

    def get_enabled_transitions(self, marking: List[int]) -> List[str]:
        """
        Returns a list of transitions that are enabled under the given marking.
        """
        return [t for t in self.transitions if self.is_enabled(t, marking)]

    def fire_transition(self, transition: str, marking: List[int]) -> List[int]:
        """
        Fire a transition and return the new marking.
        Raises ValueError if transition cannot be fired.
        """
        if not self.is_enabled(transition, marking):
            raise ValueError(f"Transition {transition} cannot be fired")
        new_marking = copy.deepcopy(marking)
        # Remove tokens from input places
        for place, weight in self.transitions[transition]['in'].items():
            idx = self.places.index(place)
            new_marking[idx] -= weight
        # Add tokens to output places
        for place, weight in self.transitions[transition]['out'].items():
            idx = self.places.index(place)
            new_marking[idx] += weight
        return new_marking


# =========================================
# Coverability Tree class
# =========================================
class CoverabilityTree:
    """
    Implements the Karp-Miller algorithm to generate the coverability tree of a Petri net.
    Handles ω (infinity) logic for unbounded places.
    """
    class TreeNode:
        """
        Represents a node in the coverability tree.
        """
        def __init__(self, marking: List, node_id: int, tag: str = "new"):
            self.marking = marking              # Marking at this node
            self.node_id = node_id              # Unique node id
            self.tag = tag                      # 'new', 'processed', 'old', 'dead-end'
            self.parent = None                  # Parent node
            self.children = []                  # List of child nodes
            self.transition = None              # Transition used to reach this node
            self.path_to_root = []              # Path from root to this node

    def __init__(self, petri_net: PetriNetwork):
        self.petri_net = petri_net
        self.nodes = []  # List of all nodes
        self.edges = []  # List of edges (parent_id, child_id, transition)
        self.root = None

    def compare_markings(self, m1: List[int], m2: List[int]) -> Tuple[bool, bool, bool]:
        """
        Compare two markings m1 and m2.
        Returns (coverable, equal, greater)
        """
        coverable, equal, greater = True, True, False
        for i in range(len(m1)):
            if m1[i] == float('inf'):
                if m2[i] != float('inf'):
                    greater = True
                continue
            if m2[i] == float('inf'):
                coverable = False
                equal = False
                continue
            if m1[i] > m2[i]:
                greater = True
                equal = False
            elif m1[i] < m2[i]:
                coverable = False
                equal = False
        return coverable, equal, greater

    def apply_omega(self, m_prime: List[int], m_ancestor: List[int]) -> List[int]:
        """
        Replace values with ω where the current marking exceeds an ancestor's marking.
        """
        result = copy.deepcopy(m_prime)
        for i in range(len(result)):
            if result[i] != float('inf') and m_ancestor[i] != float('inf') and result[i] > m_ancestor[i]:
                result[i] = float('inf')  # Mark as unbounded
        return result

    def build_tree(self):
        """
        Build the coverability tree using Karp-Miller algorithm.
        """
        node_counter = 0
        root = self.TreeNode(self.petri_net.initial_marking, node_counter, "new")
        root.path_to_root = [root]
        self.root = root
        self.nodes.append(root)
        node_counter += 1

        new_nodes = [root]  # Queue of nodes to process
        while new_nodes:
            current = new_nodes.pop(0)
            current.tag = "processed"

            # Check if current marking already exists in ancestor nodes
            for anc in current.path_to_root[:-1]:
                _, equal, _ = self.compare_markings(current.marking, anc.marking)
                if equal:
                    current.tag = "old"
                    break
            if current.tag == "old":
                continue

            enabled = self.petri_net.get_enabled_transitions(current.marking)
            if not enabled:
                current.tag = "dead-end"
                continue

            # Process each enabled transition
            for t in enabled:
                # Avoid firing ω directly; substitute with large number
                firing_marking = [1000 if m == float('inf') else m for m in current.marking]
                m_prime = self.petri_net.fire_transition(t, firing_marking)
                # Restore ω where needed
                for i, m in enumerate(current.marking):
                    if m == float('inf'):
                        m_prime[i] = float('inf')

                # Apply ω logic based on ancestors
                for anc in current.path_to_root:
                    coverable, equal, _ = self.compare_markings(m_prime, anc.marking)
                    if coverable and not equal:
                        m_prime = self.apply_omega(m_prime, anc.marking)
                        break

                # Add new node to tree
                new_node = self.TreeNode(m_prime, node_counter, "new")
                new_node.parent = current
                new_node.transition = t
                new_node.path_to_root = current.path_to_root + [new_node]
                current.children.append(new_node)
                self.nodes.append(new_node)
                new_nodes.append(new_node)
                self.edges.append((current.node_id, new_node.node_id, t))
                node_counter += 1

    def tree_to_text(self) -> str:
        """
        Convert the tree structure into a textual representation for display.
        """
        result = []

        def recurse(node, level=0):
            indent = "  " * level
            m_str = ["ω" if m == float('inf') else str(m) for m in node.marking]
            info = f"{indent}Node {node.node_id}: [{', '.join(m_str)}]"
            if node.parent:
                info += f"  (← {node.transition} from Node {node.parent.node_id})"
            if node.tag != "processed":
                info += f" [{node.tag}]"
            result.append(info)
            for child in node.children:
                recurse(child, level + 1)

        recurse(self.root)
        return "\n".join(result)

    def analyze_properties(self) -> str:
        """
        Analyze and report network properties:
        - Boundedness
        - Dead-end nodes
        - Old nodes
        """
        bounded = True
        unbounded_places = []
        dead_end_nodes = []
        old_nodes = []

        for node in self.nodes:
            for i, m in enumerate(node.marking):
                if m == float('inf'):
                    bounded = False
                    place_name = self.petri_net.places[i]
                    if place_name not in unbounded_places:
                        unbounded_places.append(place_name)
            if node.tag == "dead-end":
                dead_end_nodes.append(node)
            if node.tag == "old":
                old_nodes.append(node)

        result = []
        if bounded:
            result.append("✓ Network is BOUNDED (all places are bounded)")
        else:
            result.append(f"✗ Network is UNBOUNDED (unbounded places: {unbounded_places})")
        if dead_end_nodes:
            result.append(f"✗ Dead-end nodes found: {len(dead_end_nodes)}")
        else:
            result.append("✓ No dead-end nodes")
        if old_nodes:
            result.append(f"✓ Old nodes found: {len(old_nodes)}")
        else:
            result.append("✓ No old nodes")
        return "\n".join(result)


# =========================================
# GUI Application
# =========================================
class PetriApp:
    """
    Simple Tkinter GUI for user input of Petri net and generating Karp-Miller tree.
    """
    def __init__(self, master):
        self.master = master
        master.title("Karp-Miller Petri Network Analyzer")

        # Input fields for places and marking
        tk.Label(master, text="Places (comma-separated):").grid(row=0, column=0)
        self.entry_places = tk.Entry(master, width=50)
        self.entry_places.grid(row=0, column=1)

        tk.Label(master, text="Initial Marking (comma-separated):").grid(row=1, column=0)
        self.entry_marking = tk.Entry(master, width=50)
        self.entry_marking.grid(row=1, column=1)

        # Input for transitions as a simple string
        tk.Label(master, text="Transitions (pre/post) format: t1:P0=1;P1=2->P2=1,...").grid(row=2, column=0)
        self.entry_transitions = tk.Entry(master, width=50)
        self.entry_transitions.grid(row=2, column=1)

        # Button to generate the tree
        tk.Button(master, text="Generate Tree", command=self.generate_tree).grid(row=3, column=0, columnspan=2)

        # Output box
        self.text_output = scrolledtext.ScrolledText(master, width=100, height=30)
        self.text_output.grid(row=4, column=0, columnspan=2)

    def generate_tree(self):
        """
        Parse user input, build Petri net and coverability tree, display results.
        """
        try:
            # Parse places
            places = [p.strip() for p in self.entry_places.get().split(',')]
            # Parse initial marking
            initial_marking = [int(x.strip()) for x in self.entry_marking.get().split(',')]
            # Parse transitions
            transitions_input = self.entry_transitions.get().split(',')
            transitions = {}
            for t in transitions_input:
                t_name, rest = t.split(':')
                pre_str, post_str = rest.split('->')
                pre = {}
                post = {}
                for p in pre_str.split(';'):
                    if '=' in p:
                        place, val = p.split('=')
                        pre[place.strip()] = int(val)
                for p in post_str.split(';'):
                    if '=' in p:
                        place, val = p.split('=')
                        post[place.strip()] = int(val)
                transitions[t_name.strip()] = {'in': pre, 'out': post}

            # Build Petri net and coverability tree
            net = PetriNetwork(places, transitions, initial_marking)
            tree = CoverabilityTree(net)
            tree.build_tree()

            # Display results
            self.text_output.delete('1.0', tk.END)
            self.text_output.insert(tk.END, "=== COVERABILITY TREE ===\n")
            self.text_output.insert(tk.END, tree.tree_to_text() + "\n\n")
            self.text_output.insert(tk.END, "=== PROPERTIES ===\n")
            self.text_output.insert(tk.END, tree.analyze_properties() + "\n")

        except Exception as e:
            messagebox.showerror("Error", f"Invalid input format:\n{e}")


# =========================================
# Main
# =========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PetriApp(root)
    root.mainloop()
