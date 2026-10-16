import type { Nodes as HastNodes } from "hast"
import type { Definition, Nodes, Root, RootContent } from "mdast"
import { findAndReplace } from "mdast-util-find-and-replace"
import { toHast } from "mdast-util-to-hast"
import { toString } from "mdast-util-to-string"
import { toHtml } from "hast-util-to-html"

export type Prose = RootContent[]

export function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error("content must be an object")
  return value as Record<string, unknown>
}
export function fields(value: Record<string, unknown>, allowed: string[]): void {
  for (const key of Object.keys(value))
    if (!allowed.includes(key)) throw new Error(`unknown content field: ${key}`)
}
export function string(value: unknown): string {
  if (typeof value !== "string") throw new Error("content requires a string")
  return value
}
export function safeUrl(value: unknown, base = "https://nishantkhurana.me/digests/"): string {
  const input = string(value)
  if (/[\u0000-\u0020\u007f\\]/.test(input) || input.startsWith("//")) throw new Error("unsafe URL")
  if (input.startsWith("#")) return input
  const url = new URL(input, base)
  if (!["https:", "http:", "mailto:"].includes(url.protocol) || url.username || url.password)
    throw new Error("unsafe URL")
  return /^[a-z][a-z0-9+.-]*:/i.test(input) ? input : url.href
}

function decodeNode(value: unknown): RootContent {
  const node = object(value)
  const type = string(node.type)
  const children = () => decodeProse(node.children)
  switch (type) {
    case "text":
    case "inlineCode":
      fields(node, ["type", "value"])
      return { type, value: string(node.value) }
    case "code":
      fields(node, ["type", "value", "lang", "meta"])
      return {
        type,
        value: string(node.value),
        lang: node.lang === null ? null : string(node.lang),
        meta: node.meta === null ? null : string(node.meta),
      }
    case "break":
    case "thematicBreak":
      fields(node, ["type"])
      return { type }
    case "image":
      fields(node, ["type", "url", "title", "alt"])
      return {
        type,
        url: safeUrl(node.url),
        title: node.title === null ? null : string(node.title),
        alt: node.alt === null ? null : string(node.alt),
      }
    case "paragraph":
    case "emphasis":
    case "strong":
    case "link":
    case "heading":
    case "blockquote":
    case "list":
    case "listItem": {
      const permitted = ["type", "children"]
      if (type === "link") permitted.push("url", "title")
      if (type === "heading") permitted.push("depth")
      if (type === "list") permitted.push("ordered", "start", "spread")
      if (type === "listItem") permitted.push("spread", "checked")
      fields(node, permitted)
      const parsed: { type: string; children: RootContent[] } & Record<string, unknown> = {
        type,
        children: children(),
      }
      if (type === "link") {
        parsed.url = safeUrl(node.url)
        parsed.title = node.title === null ? null : string(node.title)
      }
      if (type === "heading") {
        if (typeof node.depth !== "number" || ![1, 2, 3, 4, 5, 6].includes(node.depth))
          throw new Error("invalid prose heading")
        parsed.depth = node.depth
      }
      if (type === "list" || type === "listItem") {
        if (typeof node.spread !== "boolean") throw new Error("invalid prose list")
        parsed.spread = node.spread
      }
      if (type === "list") {
        if (
          typeof node.ordered !== "boolean" ||
          (node.start !== null &&
            (typeof node.start !== "number" || !Number.isSafeInteger(node.start)))
        )
          throw new Error("invalid prose list")
        parsed.ordered = node.ordered
        parsed.start = node.start
      }
      if (type === "listItem") {
        if (node.checked !== null && typeof node.checked !== "boolean")
          throw new Error("invalid prose list item")
        parsed.checked = node.checked
      }
      // The allowlist above validates each field before the mdast serializer consumes it.
      return parsed as RootContent
    }
    default:
      throw new Error(`unsupported prose node: ${type}`)
  }
}

export function decodeProse(value: unknown): Prose {
  if (!Array.isArray(value)) throw new Error("prose must be an array")
  return value.map(decodeNode)
}

export function normalizeProse(
  children: RootContent[],
  definitions: Definition[],
  base: string,
): Prose {
  const tree: Root = { type: "root", children: structuredClone(children) }
  const references = new Map(definitions.map((d) => [d.identifier, d]))
  findAndReplace(tree, [
    /\[\[([^\]\n]+)\]\]/g,
    (_match, value: string) => {
      const [target = "", label] = value.split("|", 2)
      if (!target || /[\u0000-\u001f\\]/.test(target) || target.split("/").includes(".."))
        throw new Error("unsafe wikilink")
      const [path = "", fragment] = target.split("#", 2)
      return {
        type: "link",
        url: `https://nishantkhurana.me/${path.replace(/\.md$/, "").split("/").map(encodeURIComponent).join("/")}${fragment ? `#${encodeURIComponent(fragment)}` : ""}`,
        title: null,
        children: [{ type: "text", value: label ?? target }],
      }
    },
  ])
  function clean(node: Nodes): unknown {
    switch (node.type) {
      case "definition":
        return null
      case "html":
        return node.value.startsWith("<!--") ? null : { type: "text", value: node.value }
      case "text":
      case "inlineCode":
        return { type: node.type, value: node.value }
      case "code":
        return {
          type: node.type,
          value: node.value,
          lang: node.lang ?? null,
          meta: node.meta ?? null,
        }
      case "break":
      case "thematicBreak":
        return { type: node.type }
      case "image":
        return {
          type: node.type,
          url: safeUrl(node.url, base),
          title: node.title ?? null,
          alt: node.alt ?? null,
        }
      case "imageReference": {
        const ref = references.get(node.identifier)
        if (!ref) throw new Error("unresolved image reference")
        return {
          type: "image",
          url: safeUrl(ref.url, base),
          title: ref.title ?? null,
          alt: node.alt ?? null,
        }
      }
      case "linkReference": {
        const ref = references.get(node.identifier)
        if (!ref) throw new Error("unresolved link reference")
        return {
          type: "link",
          url: safeUrl(ref.url, base),
          title: ref.title ?? null,
          children: node.children.map(clean).filter((n) => n !== null),
        }
      }
      case "paragraph":
      case "emphasis":
      case "strong":
      case "link":
      case "heading":
      case "blockquote":
      case "list":
      case "listItem": {
        const result: Record<string, unknown> = {
          type: node.type,
          children: node.children.map(clean).filter((n) => n !== null),
        }
        if (node.type === "link") {
          result.url = safeUrl(node.url, base)
          result.title = node.title ?? null
        }
        if (node.type === "heading") result.depth = node.depth
        if (node.type === "list" || node.type === "listItem") result.spread = node.spread ?? false
        if (node.type === "list") {
          result.ordered = node.ordered ?? false
          result.start = node.start ?? null
        }
        if (node.type === "listItem") result.checked = node.checked ?? null
        return result
      }
      default:
        throw new Error(`unsupported authored prose: ${node.type}`)
    }
  }
  return decodeProse(tree.children.map(clean).filter((node) => node !== null))
}
export function proseHtml(prose: Prose, anchors: string[] = []): string {
  const tree = toHast({ type: "root", children: prose })
  let index = 0
  function identify(node: HastNodes): void {
    if (node.type === "element" && /^h[1-6]$/.test(node.tagName)) {
      const id = anchors[index++]
      if (id !== undefined) node.properties.id = id
    }
    if ("children" in node) node.children.forEach(identify)
  }
  identify(tree)
  return toHtml(tree, { characterReferences: { useNamedReferences: true } })
}
export function proseText(prose: Prose): string {
  return prose
    .map((node) => toString(node))
    .filter(Boolean)
    .join("\n\n")
}
