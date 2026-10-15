import type { Edition } from "../lib/digests"
import type { ChartPoint, StoryVisual } from "../lib/editorial"
import { xmlEscape as escape } from "./format"

function pointValue(point: ChartPoint): string {
  const value =
    point.value > 0 && (point.value < 0.000001 || point.value >= 1e12)
      ? String(point.value)
      : new Intl.NumberFormat("en-US", { maximumSignificantDigits: 21 }).format(point.value)
  switch (point.qualifier) {
    case "exact":
      return value
    case "approximate":
      return `~${value}`
    case "greater-than":
      return `>${value}`
    case "at-least":
      return `≥${value}`
    default: {
      const exhaustive: never = point.qualifier
      return exhaustive
    }
  }
}

export function renderVisual(visual: StoryVisual): string {
  const citation = `<a href="${escape(visual.source.url)}">${escape(visual.source.label)}</a>`
  const caption = `${escape(visual.caption)} <span class="visual-source">Source: ${citation}.</span>`
  switch (visual.kind) {
    case "image":
      return `<figure class="story-visual image-visual" data-story-visual="image"><img src="${escape(visual.src)}" width="${visual.width}" height="${visual.height}" alt="${escape(visual.alt)}" loading="lazy" decoding="async" referrerpolicy="no-referrer"><figcaption>${caption} <span class="visual-credit">Image: ${escape(visual.credit)}.</span></figcaption></figure>`
    case "bar": {
      const maximum = Math.max(...visual.points.map((point) => point.value))
      const bars = visual.points
        .map(
          (point) =>
            `<li class="bar-point" data-chart-value="${point.value}" data-chart-qualifier="${point.qualifier}"><strong class="bar-value">${escape(pointValue(point))}</strong><div class="bar-track" aria-hidden="true"><span class="bar-fill" style="height:${(point.value / maximum) * 100}%"></span></div><span class="bar-label">${escape(point.label)}</span></li>`,
        )
        .join("")
      return `<figure class="story-visual bar-visual" data-story-visual="bar"><p class="chart-title">${escape(visual.title)} <span class="chart-unit">${escape(visual.unit)}</span></p><ul class="bar-chart">${bars}</ul><figcaption>${caption}</figcaption></figure>`
    }
    default: {
      const exhaustive: never = visual
      return exhaustive
    }
  }
}

export function renderEditionHtml(edition: Edition): string {
  if (edition.kind === "legacy" || !edition.activeStories.some((story) => story.editorial))
    return edition.html
  let inBrief = false
  return edition.activeStories
    .map((story) => {
      const briefHeading = story.kind === "brief" && !inBrief ? "<h2>In brief</h2>" : ""
      if (story.kind === "brief") inBrief = true
      const level = story.kind === "brief" ? "h3" : "h2"
      const editorial = story.editorial
      return `${briefHeading}<section>${editorial ? `<p class="kicker">${escape(editorial.section)}</p>` : ""}<${level}>${escape(story.headline)}</${level}>${editorial?.deck ? `<p class="deck">${escape(editorial.deck)}</p>` : ""}${editorial?.visual ? renderVisual(editorial.visual) : ""}${story.html}</section>`
    })
    .join("\n")
}
