# Proposal 21: The Senate

## Philosophy
"The Senate" visualizes the debate as a **Galactic Council**. The AI agents are not just text generators; they are distinct, high-ranking delegates in a futuristic chamber. The Judge sits elevated in the center.

## Design Tokens

### Aesthetic
- **Theme**: High-Tech Political Thriller / Star Wars Prequels / Mass Effect Citadel.
- **Perspective**: First-person view from the "Audience" looking up at the podiums.

### Colors
- **Atmosphere**: `bg-slate-900` with volumetric lighting (CSS radial gradients).
- **Delegates**:
  - Orthodox: `cyan` / `blue` (Cold logic).
  - Heretic: `red` / `orange` (Fiery dissent).
  - Skeptic: `amber` / `yellow` (Searchlight/Inquiry).
  - Judge: `white` / `silver` (Pure neutrality).

### Typography
- **Font**: `Cinzel` (Headers) + `Orbitron` (Data).
- **Style**: Majestic, wide letter-spacing.

## Key Components

### 1. The Pods
Each agent resides in a floating "Pod".
- **Active State**: The Pod floats higher and glows brighter.
- **Passive State**: Dimmed, receded.

### 2. The Halo (Judge)
The Judge is represented by a massive holographic ring or "Eye" at the top center. It pulses when processing verdict.

### 3. The Transcript (Hologram)
Arguments don't appear in a flat list. They are projected into the center of the room as a "Holographic Scroll".

## UX Flow
1.  **Opening**: The chamber lights up. Pods ascend.
2.  **Debate**: Camera (focus) shifts slightly towards the active speaker (CSS Transforms).
3.  **Judgment**: The room dims. The Judge's Halo fires a "beam" of verdict color (Green/Red) onto the docket.

## Why this works?
It gives **personality** and **gravitas** to the agents. It makes the user feel like a witness to history.
