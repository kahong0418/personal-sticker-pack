---
name: personal-sticker-pack
description: Turn a few photos of yourself (or you and your partner, friend, team) into illustrated WhatsApp sticker packs that still look like you. Guides the whole run, from picking reference photos, choosing a style and an expression list, to writing a generation brief for any image model (ChatGPT, Codex, Gemini) and packing the results into 512×512 WebP files under 100KB with a tray icon and an overview sheet. Use when the user says "make stickers of me", "做我的 sticker", "我的形象表情包", "个人 IP sticker", "WhatsApp sticker pack", "情侣 sticker", or hands over photos and asks for stickers.
---

# Personal Sticker Pack

You help the user get a sticker pack of **themselves**, one that friends recognise at a glance.
You do not draw the images yourself. You write the brief, the user (or an image tool they have) generates, and you check and pack the results.

The whole run is five steps. Do them in order and say which step you are on.

## Step 1 · Reference photos

Ask for **3 to 8 photos** of each person who will appear.

- Face clearly visible, good light, no sunglasses. Front, three-quarter and smiling shots are best.
- Recent photos only. If their hair or glasses changed, the current look wins.
- One photo works but drifts more. Say so, and use it anyway if that is all they have.

Then write down each person's **identity markers**: the two or three things that make them recognisable in a cartoon (e.g. buzz cut + thick black square glasses; shoulder-length wavy hair + dimples). These markers go into every prompt and every check. Confirm them with the user in one line.

Also fix **one outfit per person** for the whole pack. Same clothes across stickers makes the pack feel like one character.

⛔ Never use someone's likeness without them knowing. For a couple or friend pack, the user confirms the other person is fine with it.

## Step 2 · Style and expressions

Show the user the shortlist in `references/styles.md` and let them pick 1 to 3 styles. Recommend first, then offer alternatives. If they pick several, each style becomes its own pack.

Pick the expression list from `references/expressions.md` (12 per pack is the sweet spot; WhatsApp allows 3 to 30). Adjust to the user's life: a trainer gets "holding a mic", a parent gets "kids asleep finally".

Text on stickers: only for the relatable / scene style, one short line each, copied exactly. Other styles stay text-free, which also keeps them usable in any language.

## Step 3 · Generation brief

Fill in `references/brief-template.md` and give it to the user as one file. It works pasted into ChatGPT (attach the photos), handed to Codex, or sent to any model that accepts reference images.

The brief must carry, for every sticker:
- the identity markers and the fixed outfit
- the style line from `styles.md`
- "transparent background, white die-cut outline, character centred with margin"
- the one action / expression, and the exact text if any

And these bans, which come from real failures:
- ⛔ do not make the face thinner or more pointed than the photos
- ⛔ do not change hairstyle or glasses
- ⛔ do not mirror-flip an image to get the other hand (the face becomes a mirror image)
- ⛔ no extra text, logos or watermarks
- for two people: say which person in the photo is who, and that their hands must not merge

Tell the user to **generate sticker 01 of each pack first** and check it looks like them before generating the rest. One good first image saves a whole wasted batch.

If the user later makes a second pack with the same person (e.g. a couple pack), point the brief at the finished stickers from the first pack as the reference for that person, not at an old photo. The character should stay the same across packs.

## Step 4 · Pack

Put the generated images in one folder per pack, named in order (`01.png`, `02.png`, ...). Then run `scripts/pack.py` from this skill's folder, using its absolute path (the user's working directory is not the skill folder):

```bash
python3 <this-skill-folder>/scripts/pack.py <input-folder> <output-folder> --name "My Pack"
```

It needs Pillow (`python3 -m pip install pillow`). What it does:
- removes a plain white or flat-colour background if the image came back without transparency, and redraws the white outline (it says so; check the edges)
- rejects photo, gradient or fake-checkerboard backgrounds: regenerate those with a transparent background
- trims, centres and pads every image to 512×512
- writes a PNG and a WebP per sticker, squeezing each WebP under 100KB
- makes a 96×96 tray icon from the first sticker (or `--tray file`)
- makes an `overview.png` grid with numbers
- exits non-zero and says why if anything breaks a WhatsApp rule

## Step 5 · Check, then hand over

Open `overview.png` and look at it yourself. Then zoom into the risky ones. A script passing does not mean the pack is good.

Check every sticker for:
1. **Looks like them**: identity markers present, face not slimmed, same character across the pack.
2. **Hands**: count fingers on hearts, OK signs, pointing, praying hands, hand-holding.
3. **Text** (if any): every character exactly as written, nothing garbled.
4. **Edges**: outline complete, hair not cut off by the background removal.

Redo only the stickers that fail a check. A slightly odd pose that still reads fine stays.

Then zip the output's `png/` folder together with `tray.png`, hand that zip over, and walk the user through `references/install-whatsapp.md`. Most sticker apps take the PNGs and convert them; the `webp/` folder is there for tools that want WhatsApp's final format directly.

## Good to know

- Reply in the user's language. Keep the generation brief in English unless their image tool works better in another language; text that goes ON a sticker stays in the language they chat in.
- Privacy, said plainly: this skill uploads nothing by itself, but the photos are read by Claude and sent to whichever image tool the user picks. Generated likenesses of real people are personal data; keep outputs local unless the user decides to share them.
- Do not copy another person's sticker look or a known character. Use the style list, not "make it like X's stickers".
