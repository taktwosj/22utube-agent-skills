(() => {
  "use strict";
  const script = document.currentScript;
  const tokenUrl = script?.dataset.tokens || "style_tokens.json";
  const setVar = (name, value, unit = "") => {
    if (value !== undefined && value !== null) {
      document.documentElement.style.setProperty(name, `${value}${unit}`);
    }
  };
  fetch(tokenUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`style_tokens load failed: ${response.status}`);
      return response.json();
    })
    .then((tokens) => {
      setVar("--canvas-width", tokens.canvas.width, "px");
      setVar("--canvas-height", tokens.canvas.height, "px");
      setVar("--canvas-background", tokens.canvas.background);
      setVar("--safe-top", tokens.safeArea.top, "px");
      setVar("--safe-right", tokens.safeArea.right, "px");
      setVar("--safe-bottom", tokens.safeArea.bottom, "px");
      setVar("--safe-left", tokens.safeArea.left, "px");
      setVar("--frame-top-height", tokens.frame.topHeight, "px");
      setVar("--frame-bottom-height", tokens.frame.bottomHeight, "px");
      setVar("--frame-border-width", tokens.frame.borderWidth, "px");
      setVar("--frame-border-color", tokens.frame.borderColor);
      setVar("--frame-top-color", tokens.frame.topColor);
      setVar("--frame-bottom-color", tokens.frame.bottomColor);
      setVar("--focus-color", tokens.focusLines.color);
      setVar("--focus-opacity", tokens.focusLines.opacity);
      setVar("--focus-thickness", tokens.focusLines.thickness, "px");
      setVar("--chapter-number-x", tokens.chapter.numberX, "px");
      setVar("--chapter-number-y", tokens.chapter.numberY, "px");
      setVar("--chapter-number-size", tokens.chapter.numberSize, "px");
      setVar("--chapter-title-x", tokens.chapter.titleX, "px");
      setVar("--chapter-title-y", tokens.chapter.titleY, "px");
      setVar("--chapter-title-width", tokens.chapter.titleWidth, "px");
      setVar("--chapter-title-size", tokens.chapter.titleSize, "px");
      setVar("--chapter-title-color", tokens.chapter.titleColor);
      setVar("--source-label-x", tokens.source.labelX, "px");
      setVar("--source-label-y", tokens.source.labelY, "px");
      setVar("--source-label-size", tokens.source.labelSize, "px");
      setVar("--source-date-x", tokens.source.dateX, "px");
      setVar("--source-date-y", tokens.source.dateY, "px");
      setVar("--source-date-size", tokens.source.dateSize, "px");
      setVar("--comment-x", tokens.comment.x, "px");
      setVar("--comment-y", tokens.comment.y, "px");
      setVar("--comment-width", tokens.comment.width, "px");
      setVar("--comment-size", tokens.comment.size, "px");
      setVar("--subscribe-x", tokens.subscribe.x, "px");
      setVar("--subscribe-y", tokens.subscribe.y, "px");
      setVar("--subscribe-width", tokens.subscribe.width, "px");
      setVar("--subscribe-size", tokens.subscribe.size, "px");
      setVar("--caption-band-x", tokens.captionBand.x, "px");
      setVar("--caption-band-y", tokens.captionBand.y, "px");
      setVar("--caption-band-width", tokens.captionBand.width, "px");
      setVar("--caption-band-height", tokens.captionBand.height, "px");
      setVar("--caption-band-opacity", tokens.captionBand.opacity);
      setVar("--caption-band-color", tokens.captionBand.color);
      setVar("--caption-font-family", tokens.captionText.fontFamily);
      setVar("--caption-x", tokens.captionText.x, "px");
      setVar("--caption-y", tokens.captionText.y, "px");
      setVar("--caption-width", tokens.captionText.width, "px");
      setVar("--caption-height", tokens.captionText.height, "px");
      setVar("--caption-font-size", tokens.captionText.fontSize, "px");
      setVar("--caption-line-height", tokens.captionText.lineHeight);
      setVar("--caption-outline", tokens.captionText.outlineWidth, "px");
      setVar("--caption-color", tokens.captionText.color);
      setVar("--caption-outline-color", tokens.captionText.outlineColor);
      setVar("--animation-enter", tokens.animation.enterSeconds, "s");
      setVar("--animation-exit", tokens.animation.exitSeconds, "s");
      setVar("--focus-pulse", tokens.animation.focusPulseSeconds, "s");
      setVar("--animation-translate-y", tokens.animation.translateY, "px");
      setVar("--z-media", tokens.zIndex.media);
      setVar("--z-frame", tokens.zIndex.frame);
      setVar("--z-focus-lines", tokens.zIndex.focusLines);
      setVar("--z-caption-band", tokens.zIndex.captionBand);
      setVar("--z-metadata", tokens.zIndex.metadata);
      setVar("--z-caption-text", tokens.zIndex.captionText);
      document.documentElement.dataset.tokensLoaded = "true";
    })
    .catch((error) => {
      document.documentElement.dataset.tokensLoaded = "false";
      console.error(error);
    });
})();
