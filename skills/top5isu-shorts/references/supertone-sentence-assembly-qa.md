# Supertone Sentence Assembly QA

## Purpose

Use this reference for Korean TOP5 narration after the fixed Supertone voice identity has passed. The production unit is one grammatical sentence, not one source line and not a multi-sentence paragraph.

## User-provided SRT conversion

When the operator supplies a final audio file plus an SRT whose captions are
written as Korean pronunciation text, keep the timing authority but do not use
the pronunciation spellings as visible captions.

1. Preserve the supplied file unchanged as `subtitles_spoken_original.srt`.
2. Create a separate `subtitles_display.srt` with identical cue indices, start
   times, and end times.
3. Restore display notation without changing the spoken fact:

```text
이천이십육년 -> 2026년
오 위 / 사 위 / 삼 위 / 이 위 / 일 위 -> 5위 / 4위 / 3위 / 2위 / 1위
에이아이 -> AI
케이비증권 -> KB증권
이백사십일조 원 -> 241조 원
```

4. Reflow only the visible text to a maximum of two lines per cue.
5. Require zero overlaps, the same cue count, and final SRT end within 50 ms of
   the supplied audio duration.
6. Confirm no pronunciation-only numeral or abbreviation tokens remain in the
   display SRT.
7. Use `subtitles_display.srt` for CapCut captions; keep
   `subtitles_spoken_original.srt` only as timing/source evidence.

```text
spoken_srt_timing_authority=true
display_srt_text_authority=true
spoken_and_display_srt_separate=true
```

## Required pipeline

1. Keep two text authorities:
   - `tts_copy_text.txt`: visible/caption factual authority.
   - `tts_spoken_copy.txt`: pronunciation-only rendering with identical facts.
2. Split `tts_spoken_copy.txt` on sentence-ending punctuation. If one line contains `안녕하세요. 오늘의 탑파이브 주제인데요.`, create two clips.
3. Generate one WAV per sentence using the locked voice ID/model/language.
4. Save one manifest item per sentence: index, expected text, path, duration, SHA-256, start, and end.
5. Run Korean ASR on every sentence clip before joining.
6. Mark each clip `PASS` or `REPAIR`; never infer sentence quality from the final track alone.
7. Regenerate only `REPAIR` indices. Keep all passing clips byte-identical.
8. Rebuild concat, timings, captions, duration, loudness output, and hashes after any replacement.
9. Run full-track ASR and direct listen-through. The operator's audible report is a hard failure even when ASR passes.

## Per-sentence checks

Check all applicable fields, not only adjacent duplicate tokens:

- opening/greeting is complete;
- company name is not repeated or mutated;
- rank is correct;
- every amount is correct;
- no inserted word or filler;
- no repeated word, syllable, or number tail;
- sentence-final verb is present;
- no clipping at the start or end.

Examples of failures:

```text
글로벌 -> 글로벌글로벌
실적 -> 실실적
삼성전자 -> 삼성전전자 / 삼성성전자
327조 -> 377조
357조 원 -> 357주원
반전은 내년입니다 -> extra inserted words
```

## Pronunciation-copy repair patterns

Change only the spoken copy; preserve visible captions and factual values.

```text
2026 -> 이천이십육년
TOP5 -> 탑파이브
AI -> 에이아이
327조 원 -> 삼백 이십 칠 조 원
357조 원 -> 삼백 오십 칠 조 원
```

When word adjacency creates a false phrase, reorder the spoken sentence while retaining meaning:

```text
BAD: 영업이익은 삼백 이십 칠 조 원 전망입니다.
     # `조 원 전망` may sound like `조언 전망`
GOOD: 영업이익 전망은 삼백 이십 칠 조 원입니다.
```

If a company name repeatedly stutters:

1. regenerate that sentence once;
2. try pronunciation spacing in the spoken copy;
3. if the provider has a deterministic fixed defect, use a semantically safe spoken short form only when the exact company name remains visible in captions and the operator accepts the audio;
4. never change the displayed company or amount to hide a TTS problem.

## Selective regeneration contract

Support a repair-index list such as:

```text
REPAIR_LINES=2,8,10
```

When a repair list is present:

- do not delete other sentence WAVs;
- regenerate only listed indices;
- reconstruct the ordered manifest from current expected sentences;
- rebuild final audio and timings;
- rerun ASR only on repaired clips, then perform one final full-track QA.

If sentence insertion/removal shifts indices, perform a controlled full sentence rebuild and repeat sentence QA; do not reuse files under mismatched indices.

## Joining and loudness

- Use a consistent 80–150 ms gap unless the script calls for a deliberate pause.
- Never overlap sentence clips.
- Keep narration under the episode duration target without trimming speech waveforms.
- Normalize only after sentence QA and final joining.
- Re-measure integrated loudness, peak, duration, and SHA-256 after the last repair.

## Final gate

Do not proceed to subtitles, image boundaries, or CapCut until:

```text
voice_identity=PASS
sentence_count_matches=PASS
all_sentence_asr=PASS
audible_stutter_review=PASS
rank_and_amounts=PASS
final_join_order=PASS
```
