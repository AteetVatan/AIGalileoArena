# Proposal 9: Constructivist

## Philosophy
"Constructivist" is inspired by **Russian Constructivism** and **Bauhaus Architecture**. It treats the debate as a **structural engineering** feat. Arguments are concrete blocks that stack to build a "Tower of Truth". It is **bold**, **geometric**, and **unapologetically rigid**.

## Design Tokens

### Colors
- **Canvas**: `bg-stone-200` (#e7e5e4) -> Concrete / Drafting paper.
- **Construct Red**: `bg-red-600` (#dc2626) -> Action, strength, assertion.
- **Industrial Black**: `text-zinc-900` (#18181b) -> Ink, steel.
- **Blueprint Blue**: `text-blue-700` (#1d4ed8) -> Technical planning.
- **Shadows**: Hard, non-blurred shadows (`box-shadow: 4px 4px 0px black`).

### Typography
- **Headings**: `font-anton` (Anton) -> Tall, bold, poster-like.
- **Body**: `font-jetbrains-mono` (JetBrains Mono) or `font-rubik` (Rubik) -> Blocky, legible.
- **Accents**: Uppercase, tracked out.

### Visual Effects
- **Isometric Projection**: The main view is a 3D isometric grid.
- **Hard Edges**: No border-radius. Everything is a square or rectangle.
- **High Contrast**: Explicit borders, strong delineation of space.
- **Matte**: No gradients, only flat colors.

## Interaction Model
- **Construction**: New arguments animate in as blocks falling from the sky (Tetris-like) onto the stack.
- **Stability**: Weak arguments make the stack visually wobble.
- **Inspection**: User rotates the entire structure to see different "sides" (perspectives) of the argument.

## Key Components
1.  **The Site**: The isometric grid floor.
2.  **The Crane**: The input mechanism (where new prompts come from).
3.  **The Blueprint**: A 2D schematic overlay showing the logical structure.
