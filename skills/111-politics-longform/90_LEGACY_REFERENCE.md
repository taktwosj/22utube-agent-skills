# Legacy Reference

YP007, YP005, YM007, YM008, YSM, and `jungchi` are legacy references only.

Do not use any of them as the default base. Do not auto-fallback to them. Use
them only when the user explicitly promotes one in the current request or when
repairing an old project that already used that base.

Old role lineage that may help with repair:

- t1: source channel
- t2: upload date
- t3: flow strap
- t4: lower T1 commentary
- t5: subscribe line
- fixed overlay/image tracks may include focus-line and blue banner assets
- old templates may contain `bottom_topic_comments_*` or `t1_topic_texts.json`; use them as style references only, not as new episode content

If a copied draft still points to `D:\Downloads\...` for shared PNG assets,
patch the media paths to the current shared OneDrive asset paths before
validation.
