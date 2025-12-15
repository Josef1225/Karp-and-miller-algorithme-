# Karp-Miller Petri Network Analyzer

## Overview
Implements the Karp-Miller algorithm for analyzing Petri networks, which model concurrent, distributed, and parallel systems. The coverability tree allows analyzing potentially infinite networks using the special ω symbol.

## Installation
1. Install Python 3.8+
2. Run: `pip install tk`
3. Execute: `python karp_miller_gui.py`

## Quick Start Example
**Places:** `P0,P1,P2`
**Initial Marking:** `1,0,0`
**Transitions:** `t1:P0=1->P1=1,t2:P1=1->P2=1,t3:P2=1->P0=1`

## Input Format
- **Places:** Comma-separated names: `P0,P1,P2`
- **Initial Marking:** Comma-separated integers: `1,0,0`
- **Transitions:** `t_name:input_places->output_places`
  Example: `t1:P0=1->P1=1,t2:P1=1->P2=1`

## Algorithm Steps
1. Start with initial marking as root node
2. Process "new" nodes until none remain
3. For each node:
   - Check if identical to ancestor → tag "old"
   - If no enabled transitions → tag "dead-end"
   - Fire enabled transitions
   - Apply ω rule if marking covers ancestor
   - Create new child nodes

## ω Symbol Rules
- ω > n for any integer n
- ω ± n = ω
- ω ≥ ω

## Output Information
- Hierarchical coverability tree
- Boundedness analysis
- Dead-end nodes detection
- Repeated markings identification

## Example Scenarios
1. **Bounded Cycle:** No ω appears, finite states
2. **Unbounded Growth:** ω appears in markings
3. **Conflict/Choice:** Tree branches show alternatives
