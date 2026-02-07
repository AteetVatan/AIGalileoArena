# Proposal 22: Mecha Arena

## Philosophy
"Mecha Arena" gamifies the debate. It treats intellectual conflict as physical combat. This is perfect for the "Arena" in "Galileo Arena". It visualizes the strength of arguments as "Damage" and "Health".

## Design Tokens

### Aesthetic
- **Theme**: Fighting Games (Street Fighter / Tekken) / Mecha Anime (Gundam).
- **Layout**: Split screen. Player 1 (Orthodox) vs Player 2 (Heretic).

### Colors
- **UI**: High contrast, metallic textures, warning stripes.
- **P1**: `Blue` / `Cyan`.
- **P2**: `Red` / `Magenta`.
- **Judge**: `Green` (The Referee).

### Typography
- **Font**: `Russo One` (Wide, impact) + `Chakra Petch` (Angular).
- **Style**: Italicized, skewed, outlined text.

## Key Components

### 1. The HUD (Heads-Up Display)
- **Health Bars**: Represent "Confidence" or "Stability" of the argument.
- **Super Meter**: Represents "Evidence Accumulated". When full, the agent unleashes a "Citation Strike".

### 2. The Combatants
- Visual representation of two mechs facing each other.
- When an agent generates a token stream, it looks like a particle beam firing at the opponent.

### 3. The Referee (Judge)
- Appears in the center background or top overlay.
- "KO" or "WINNER" announcements correspond to the Verdict.

## UX Flow
1.  **Round Start**: "ROUND 1: FIGHT!" (Case Start).
2.  **Exchange**: Agents speak. Text bubbles appear as "attacks".
3.  **Damage**: If the Judge marks an argument as weak, that agent's health bar shakes and drops.

## Why this works?
It’s incredibly engaging. It turns abstract scoring (0-100) into a visceral "Health Bar" that everyone intuitively understands.
