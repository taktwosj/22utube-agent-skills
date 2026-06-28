# Decisive Image

Use this when a script needs image prompts, thumbnail concepts, scene stills, or production visuals.

The goal is to turn the script's decisive scene into a concrete visual. Do not draw the abstract concept.

## Required Output

```text
Decisive Image Pass
- Script anchor:
- Scene subject:
- Concrete place:
- Visible trouble:
- One object/number/action:
- Banned abstract symbols:
- Image prompt:
```

## Core Rule

```text
abstract concept -> one person -> one place -> one visible trouble -> one anchor object
```

The image must show the same person, object, number, sentence, or action that the script keeps following.

If the script anchor is "1 meter", the image should show a car barely moved in a parking lot, not a giant law book or police siren.

If the script anchor is "failure on a resume", the image should show one resume page and one person looking at it, not a trophy, ladder, or glowing city skyline.

## Ban Concept Literalism

Do not translate keywords directly into symbols.

Bad:

```text
"Japan ATM is over" -> Japan map, flag, globe, explosion, red crack, giant warning symbol
"Bitcoin regret" -> floating coin, rocket, fire, global market background
"Power isolated her" -> palace silhouette, dark storm, abstract chains
```

Better:

```text
"Japan ATM is over" -> one simple character standing at a Japanese ATM, card rejected, receipt slot empty, people waiting behind
"Bitcoin regret" -> one person staring at a phone chart after selling, small profit note on the table, price much higher on screen
"Power isolated her" -> a closed palace door, food left at the door, no person entering
```

## One Character, One Situation

Prefer a simple anonymous character, stick-figure style, or stylized 2D character when realism is not required.

Why:

- avoids uncanny AI faces and hands
- keeps focus on the situation
- makes repeated channel visuals consistent
- lets viewers project themselves into the character

Default visual subject:

```text
one simple character in a concrete location, facing one specific problem
```

Avoid:

- crowds unless the crowd creates pressure
- giant maps, flags, globes, explosions, lightning, abstract charts
- symbolic collages
- "dramatic cinematic background" with no action
- photorealistic faces when the real person is not needed or not available

## Image Prompt Formula

Use this structure:

```text
Simple stylized 2D scene, one anonymous stick-figure-like character, [specific place], [visible trouble], [anchor object/number/action clearly visible], realistic everyday situation, clean composition, no map, no flag, no globe, no abstract explosion, no symbolic collage.
```

If the channel requires a less childish look, replace "stick-figure-like" with:

```text
simple anonymous 2D character, minimal facial details, realistic body posture
```

## Examples

### Japan ATM

Bad:

```text
Japan map hit by a red lightning bolt, Japanese flag cracking, globe background
```

Good:

```text
Simple stylized 2D scene, one anonymous character standing at an ATM in Japan, card rejected on the screen, empty cash slot, two people waiting behind, small suitcase near the character, realistic everyday situation, clean composition, no map, no flag, no globe, no explosion.
```

### Drunk Parking 1 Meter

```text
Simple stylized 2D scene, one anonymous character stepping out of a car in a small villa parking lot at night, the car is only slightly repositioned inside the parking line, a police car arriving in the background, "1m" distance mark subtly visible on the ground, realistic everyday situation, no giant siren, no abstract law symbol.
```

### Failure On Resume

```text
Simple stylized 2D scene, one anonymous character sitting at a small desk in a semi-basement room, resume paper on the desk with one highlighted line about failure, bankbook showing 100,000 won beside it, dim room light, realistic everyday situation, no trophy, no luxury apartment, no glowing success ladder.
```

### Closed Door / Palace Isolation

```text
Stylized 2D historical scene, one closed palace door, a tray of food left at the door, no person entering, quiet corridor, the focus is the closed door and the untouched tray, no abstract chains, no giant palace silhouette, no fantasy lighting.
```

### Work Refusal

```text
Simple stylized 2D office scene, one tired employee standing near an elevator button, a manager holding papers and asking for help, the employee looking down at a phone calendar, realistic office hallway, clean composition, no motivational icons, no abstract stress cloud.
```

### Bitcoin Regret

```text
Simple stylized 2D scene, one person at a desk looking at a phone chart, a small note says "sold at 10M", the phone screen shows a much higher price, coffee gone cold, realistic room, no rocket, no giant coin, no fire, no globe.
```

## Visual Continuity

For a multi-image script, do not make every image a new concept.

Keep one visual thread:

```text
same character
same object
same room/location
same number on screen
same document
same button
```

Example for "failure on resume":

1. Resume paper on desk.
2. Contract papers left after partner disappears.
3. Bankbook shows 100,000 won.
4. Resume paper again, now held by a representative.
5. Same resume line returns in the ending.

## Final Test

Before accepting an image prompt, ask:

```text
Could this image exist as one frame from the actual scene?
Does it show one person dealing with one concrete trouble?
Does it contain the script anchor?
Would the viewer understand the situation without a map, flag, globe, or abstract symbol?
```

If no, reframe the image around a person, place, action, and object.
