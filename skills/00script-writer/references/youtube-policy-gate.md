# YouTube Policy Gate

Use this for any YouTube script, Shorts caption package, narration, title,
thumbnail text, description, tags, pinned comment, upload package, or production
handoff text.

This is a hard safety and monetization gate. It does not replace the persona
retention gate. The persona gate asks whether viewers understand and keep
watching; this gate asks whether YouTube policy, advertiser suitability,
metadata, source, and link risk block or require rewriting.

## Required Timing

Run or explicitly mark this gate at four points:

1. Before drafting: classify topic risk and decide whether EDSA context is
   required.
2. After first draft: scan the actual lines, scenes, claims, and implied
   instructions.
3. Before metadata: scan title, thumbnail text, description, tags, pinned
   comment, and external links.
4. Before final PASS: rerun after every material rewrite and record the verdict.

Script-only planning does not fake automation. If no production folder exists,
write `n8n status board: N/A - script-only` and `harness/check script: WAIT -
no episode production folder yet`, but still perform the written policy gate.

## Required Output

```text
YouTube Policy Gate
- policy risk tier: LOW / MEDIUM / HIGH / BLOCK
- platform safety verdict: PASS / REWRITE_REQUIRED / FAIL
- monetization verdict: GREEN / LIMITED_ADS_RISK / NO_ADS_RISK
- EDSA context: NONE / WEAK / CLEAR_IN_SCRIPT / CLEAR_IN_AUDIO_VIDEO
- metadata risk: title / thumbnail / description / tags / pinned comment / external links
- minor/audience risk:
- hate/harassment/doxxing risk:
- violence/self-harm/shock risk:
- sexual/adult/family-misleading risk:
- regulated goods/firearms/drugs/tobacco risk:
- medical/election/misinformation risk:
- copyright/source risk:
- AI repetition/scraped-content risk:
- blocking failures:
- required rewrites:
```

## Verdicts

- `LOW`: ordinary script risk. Continue after normal evidence and persona gates.
- `MEDIUM`: sensitive words or claims exist, but context is clear. Continue only
  if metadata and source checks are clean.
- `HIGH`: policy-sensitive topic. EDSA context, source separation, metadata
  scan, and final rerun are mandatory.
- `BLOCK`: do not draft or finalize until the premise is reframed.

Platform safety and monetization are separate. A video may be allowed on the
platform but still have limited ads or no ads because of language, sexual
material, violence, shock, drugs, firearms, controversial issues, sensitive
events, tobacco, hateful or derogatory framing, or unsafe behavior.

## Hard Blocks

Mark `FAIL` or `BLOCK` if the script, visible text, metadata, link, or implied
instruction includes any of these:

- Child sexual abuse material, minor sexualization, or sexual exploitation.
- Self-harm, suicide, or eating-disorder methods, locations, instructions, or
  detailed procedural cues.
- Bomb, explosive, firearm, ammunition, large-capacity magazine, homemade
  silencer, automatic-fire conversion, or safety-device removal instructions.
- Hard-drug, poison, or prescription-drug purchase links, contact details,
  suppliers, or step-by-step manufacture/use.
- Terrorist, violent extremist, or criminal organization praise, recruitment,
  fundraising, logos used for promotion, manifesto links, or raw reposts.
- Doxxing, personal information exposure, stalking, swatting, harassment
  coordination, phishing, harmful hacking, credential theft, or exploit steps.
- Hardcore pornography, non-consensual sexualization, voyeurism, or leaked nude
  framing.
- Vote suppression, false voting methods, candidate eligibility falsehoods, or
  democratic-process disruption.
- Medical claims that promote harmful cures or contradict local health authority
  guidance in a way that may cause serious harm.
- Unlicensed copyrighted content reused without transformation, commentary,
  criticism, education, or clear rights basis.
- Scam, impersonation, fake support, guaranteed-money claims, or deceptive
  external-link funneling.

Do not keep procedural detail just because the script says "do not do this."
Remove or generalize the exact method, part, dose, purchase route, exploit step,
target, supplier, contact route, or location.

## Rewrite Required

Mark `REWRITE_REQUIRED` when the premise can continue but must be safer:

- Title, thumbnail, or opening hook uses profanity, gore, sex, shock, or victim
  suffering as the main click bait.
- Metadata promises content that is not actually in the video.
- A sensitive event, disaster, war, death, criminal case, or real victim is
  treated as spectacle instead of information, prevention, or analysis.
- A family- or child-looking package contains adult themes, violence, medical
  procedures, horror, self-harm, drugs, or sexual framing.
- Hate, harassment, protected-class insult, victim mocking, dehumanizing
  metaphor, or hostile call-to-action appears.
- Dangerous behavior is shown or described without meaningful consequence,
  prevention context, or removal of copyable steps.
- Health, election, scam, finance, law, statistics, or current-event claims lack
  sources or blur fact, inference, reconstruction, and opinion.
- Finance wording sounds like buy/sell instruction instead of what to check.
- AI-generated or scraped material is repetitive, minimally transformed, or used
  to flood output.
- External links, verbal URLs, or contact paths could route viewers to regulated,
  illegal, harmful, deceptive, or infringing material.

## EDSA Context Rule

EDSA means educational, documentary, scientific, artistic, or public-interest
context. It can reduce risk only when the context is real and visible.

For high-risk topics, context must appear inside the script, audio, captions, or
video itself. Do not rely on comments, pinned comments, tags, channel
description, or hidden production notes.

Strong EDSA context includes:

- what happened, who is involved, when, where, and why it matters;
- prevention, criticism, warning, historical explanation, or public-interest
  framing;
- source separation between fact, reported fact, inference, reconstruction, and
  opinion;
- removal or blurring of copyable harm details;
- no praise, recruitment, ridicule of victims, or celebration of harm.

EDSA still does not excuse child sexual abuse material, explicit sexual assault,
beheading, perpetrator-filmed deadly/major violence, raw extremist/criminal
organization reposts, self-harm methods, bomb-making, prohibited firearm
manufacture, harmful hacking, doxxing, hard pornography, regulated-goods sales,
or spam.

## Category Scan

Check every script and metadata package against these categories:

- Inappropriate language: sexual profanity, excessive swearing, severe profanity
  in title/thumbnail, or sexual sounds.
- Sexual/adult content: sexual gratification, nudity focus, fetish, sex acts,
  non-consensual sexualization, or misleading family packaging.
- Child safety: minors in sexual, dangerous, humiliating, coerced, violent,
  drug/alcohol/tobacco, firearm, or adult-theme contexts.
- Self-harm/eating disorders: methods, locations, graphic details, triggering
  imagery, or recovery content that teaches behavior instead of support.
- Violence/shock: gore, corpses, blood, animal abuse, staged rescue, threats,
  fight glorification, graphic injury, or shock-first editing.
- Violent extremist/criminal organizations: praise, recruitment, fundraising,
  logos, manifesto links, raw reposts, or glorifying perpetrators.
- Hate/harassment: protected-class attack, dehumanization, slurs, targeted
  insults, threats, victim denial, conspiracy harassment, or doxxing.
- Dangerous acts: harmful challenges, pranks, weapons misuse, theft, evasion,
  hacking, phishing, or instructions that enable serious harm.
- Regulated goods: alcohol, nicotine, drugs, prescriptions, gambling, weapons,
  explosives, forged documents, stolen financial information, trafficking,
  prostitution, unlicensed medical services, endangered species, or organs.
- Firearms: sales, private-sale contact, manufacturing, modification, automatic
  fire conversion, large-capacity magazines, homemade silencers, or live firearm
  handling/transport.
- Misinformation: manipulated content, wrong source/date/place, census
  interference, election interference, candidate eligibility falsehoods, or
  harmful medical misinformation.
- Copyright/source: Content ID risk, takedown risk, unlicensed reuse, weak fair
  use basis, or no transformation.
- Spam/deception: engagement manipulation, comment spam, fake engagement,
  malicious clickbait, scraped content, mass AI repetition, detection evasion,
  or external-platform funneling.

## n8n Policy QA JSON Contract

When a policy QA agent, n8n node, or harness writes a machine-readable result,
use these keys:

```json
{
  "youtube_policy_gate_complete": true,
  "policy_risk_tier": "LOW|MEDIUM|HIGH|BLOCK",
  "platform_safety_verdict": "PASS|REWRITE_REQUIRED|FAIL",
  "monetization_verdict": "GREEN|LIMITED_ADS_RISK|NO_ADS_RISK",
  "edsa_context": "NONE|WEAK|CLEAR_IN_SCRIPT|CLEAR_IN_AUDIO_VIDEO",
  "metadata_flags": [],
  "hard_blocks": [],
  "rewrite_required": [],
  "source_evidence_issues": [],
  "copyright_issues": [],
  "external_link_issues": [],
  "required_fixes": [],
  "final_note": ""
}
```

The final script or caption package cannot be called `final`, `ready`,
`approved`, or `PASS` unless:

- `youtube_policy_gate_complete` is true;
- `platform_safety_verdict` is `PASS`;
- `policy_risk_tier` is not `BLOCK`;
- `hard_blocks` is empty;
- every `rewrite_required` item has been fixed and rerun;
- monetization risk has been separately labeled when relevant.

