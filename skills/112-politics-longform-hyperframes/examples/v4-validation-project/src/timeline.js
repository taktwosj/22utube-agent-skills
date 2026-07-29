window.__timelines = window.__timelines || {};

const tl = gsap.timeline({
  paused: true,
  defaults: { duration: 0.42, ease: "power3.out" },
});

const captions = gsap.utils.toArray(".caption-line");
const sceneInners = gsap.utils.toArray(".scene-inner");

function showCaption(selector, at) {
  tl.set(captions, { autoAlpha: 0 }, at);
  tl.set(selector, { autoAlpha: 1 }, at);
}

function chapterEntrance(sceneSelector, at) {
  tl.fromTo(
    `${sceneSelector} .eyebrow`,
    { y: 18, opacity: 0.45 },
    { y: 0, opacity: 1, duration: 0.35, ease: "power3.out" },
    at,
  );
  tl.fromTo(
    `${sceneSelector} .hero-title`,
    { y: 44, opacity: 0.5 },
    { y: 0, opacity: 1, duration: 0.55, ease: "power4.out" },
    at + 0.08,
  );
  tl.fromTo(
    `${sceneSelector} .hero-summary`,
    { y: 26, opacity: 0.35 },
    { y: 0, opacity: 1, duration: 0.5, ease: "power3.out" },
    at + 0.2,
  );
  tl.fromTo(
    `${sceneSelector} .chapter-box`,
    { y: 26, opacity: 0.25 },
    { y: 0, opacity: (index, element) => element.classList.contains("is-waiting") ? 0.42 : element.classList.contains("is-complete") ? 0.68 : 1, duration: 0.52, stagger: 0.07 },
    at + 0.24,
  );
  tl.fromTo(
    `${sceneSelector} .chapter-box.is-current`,
    { scale: 1 },
    { scale: 1.06, duration: 0.38, ease: "power3.out" },
    at + 0.34,
  );
}

function pulseIcon(selector, at) {
  tl.to(selector, { scale: 1.14, duration: 0.16, ease: "power4.out" }, at);
  tl.to(selector, { scale: 1, duration: 0.2, ease: "power2.out" }, at + 0.16);
}

tl.fromTo(
  "#city-background-media",
  { x: -18, scale: 1.02 },
  { x: 12, scale: 1.07, duration: 21.5, ease: "none" },
  0,
);

tl.set(sceneInners, { autoAlpha: 0 }, 0);
tl.set("#chapter-01-inner", { autoAlpha: 1 }, 0);
tl.set(captions, { autoAlpha: 0 }, 0);
showCaption("#caption-chapter-01", 0);
chapterEntrance("#chapter-01-inner", 0);

tl.set("#chapter-01-inner", { autoAlpha: 0 }, 2.5);
tl.set("#body-scene-inner", { autoAlpha: 1 }, 2.5);
tl.fromTo(
  "#body-scene-inner .chapter-rail",
  { x: -34, opacity: 0.45 },
  { x: 0, opacity: 1, duration: 0.45, ease: "power3.out" },
  2.5,
);
tl.fromTo(
  "#body-scene-inner .semantic-stage-heading",
  { y: 28, opacity: 0.35 },
  { y: 0, opacity: 1, duration: 0.5, ease: "power3.out" },
  2.56,
);
tl.set("#semantic-fact, #semantic-claim, #semantic-conclusion", { autoAlpha: 0 }, 2.5);
tl.set(".arrow-one i, .arrow-two i", { scaleX: 0 }, 2.5);

showCaption("#caption-fact", 2.8);
tl.fromTo(
  "#semantic-fact",
  { y: 20, scale: 0.96, autoAlpha: 0 },
  { y: 0, scale: 1.06, autoAlpha: 1, duration: 0.26, ease: "power4.out" },
  2.8,
);
tl.to("#semantic-fact .glow-ring", { opacity: 1, duration: 0.2 }, 2.82);
pulseIcon("#semantic-fact .semantic-icon", 2.92);

tl.to("#semantic-fact", { scale: 1, opacity: 0.46, duration: 0.24, ease: "power2.out" }, 4.5);
tl.to("#semantic-fact .glow-ring", { opacity: 0, duration: 0.2 }, 4.5);
showCaption("#caption-claim", 4.7);
tl.to(".arrow-one i", { scaleX: 1, duration: 0.48, ease: "power3.out" }, 4.7);
tl.fromTo(
  "#semantic-claim",
  { x: 28, scale: 0.96, autoAlpha: 0 },
  { x: 0, scale: 1.06, autoAlpha: 1, duration: 0.28, ease: "power4.out" },
  4.7,
);
tl.to("#semantic-claim .glow-ring", { opacity: 1, duration: 0.2 }, 4.72);
pulseIcon("#semantic-claim .semantic-icon", 4.84);

tl.to("#semantic-claim", { scale: 1, opacity: 0.46, duration: 0.24, ease: "power2.out" }, 6.4);
tl.to("#semantic-claim .glow-ring", { opacity: 0, duration: 0.2 }, 6.4);
showCaption("#caption-conclusion", 6.7);
tl.to(".arrow-two i", { scaleX: 1, duration: 0.48, ease: "power3.out" }, 6.7);
tl.fromTo(
  "#semantic-conclusion",
  { y: 24, scale: 0.96, autoAlpha: 0 },
  { y: 0, scale: 1.06, autoAlpha: 1, duration: 0.28, ease: "power4.out" },
  6.7,
);
tl.to("#semantic-conclusion .glow-ring", { opacity: 1, duration: 0.2 }, 6.72);
tl.fromTo(".conclusion-path i", { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: "power3.out" }, 6.82);
pulseIcon("#semantic-conclusion .semantic-icon", 6.86);
tl.to("#semantic-conclusion", { scale: 1, opacity: 0.5, duration: 0.24, ease: "power2.out" }, 8.2);
tl.to("#semantic-conclusion .glow-ring", { opacity: 0, duration: 0.2 }, 8.2);

tl.set("#body-scene-inner", { autoAlpha: 0 }, 8.6);
tl.set("#source-scene-inner", { autoAlpha: 1 }, 8.6);
showCaption("#caption-source", 8.6);
tl.fromTo(
  "#source-scene-inner .chapter-rail",
  { x: -28, opacity: 0.55 },
  { x: 0, opacity: 1, duration: 0.42, ease: "power3.out" },
  8.6,
);
tl.fromTo(
  ".source-frame-border",
  { scale: 0.985, opacity: 0.35 },
  { scale: 1, opacity: 1, duration: 0.48, ease: "power3.out" },
  8.6,
);
tl.fromTo(
  "#source-focus-lines",
  { scale: 0.92, opacity: 0 },
  { scale: 1, opacity: 1, duration: 0.2, ease: "power4.out" },
  9.25,
);
tl.to("#source-focus-lines", { opacity: 0, duration: 0.75, ease: "power2.out" }, 9.45);

tl.set("#source-scene-inner", { autoAlpha: 0 }, 11.5);
tl.set("#chapter-02-inner", { autoAlpha: 1 }, 11.5);
showCaption("#caption-chapter-02", 11.5);
chapterEntrance("#chapter-02-inner", 11.5);
tl.set("#chapter-02-inner", { autoAlpha: 0 }, 14.5);
tl.set("#chapter-03-inner", { autoAlpha: 1 }, 14.5);
showCaption("#caption-chapter-03", 14.5);
chapterEntrance("#chapter-03-inner", 14.5);
tl.set("#chapter-03-inner", { autoAlpha: 0 }, 17.5);
tl.set("#chapter-04-inner", { autoAlpha: 1 }, 17.5);
showCaption("#caption-chapter-04", 17.5);
chapterEntrance("#chapter-04-inner", 17.5);

tl.fromTo(
  "#chapter-04-inner .hero-title span",
  { scale: 0.96, opacity: 0.72 },
  { scale: 1, opacity: 1, duration: 0.55, ease: "power3.out" },
  18.0,
);

window.__politicsV4Timeline = tl;
window.__timelines["politics-longform-v4-validation"] = tl;
