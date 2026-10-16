import type { ChartPoint } from "./editorial.ts"

export function xmlEscape(value: string): string {
  return value.replace(/[<>&"']/g, (character) => {
    switch (character) {
      case "<":
        return "&lt;"
      case ">":
        return "&gt;"
      case "&":
        return "&amp;"
      case '"':
        return "&quot;"
      case "'":
        return "&apos;"
      default:
        return character
    }
  })
}

export function pointValue(point: ChartPoint): string {
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
