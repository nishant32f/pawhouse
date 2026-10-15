import { execFile } from "node:child_process"
import { createHash } from "node:crypto"
import { promisify } from "node:util"
import type { Definition, Heading, Nodes, Root, RootContent } from "mdast"
import { findAndReplace } from "mdast-util-find-and-replace"
import { toHast } from "mdast-util-to-hast"
import { toString } from "mdast-util-to-string"
import { toHtml } from "hast-util-to-html"
import remarkParse from "remark-parse"
import { unified } from "unified"
import { parseDocument } from "yaml"

export type Source = { label: string; url: string }
type StoryFields = {
  id: string
  headline: string
  path: string
  editionPath: string
  summary: string
  summaryHtml: string
  markdown: string
  bodyMarkdown: string
  html: string
  text: string
  sources: Source[]
}
export type ActiveStory = StoryFields & { kind: "story" | "brief" }
export type ArchivedStory = StoryFields & { kind: "archived"; correction: string }
export type Story = ActiveStory | ArchivedStory

type EditionFields = {
  date: string
  title: string
  publishedAt: string
  path: string
  readPath: string
  sourcePath: string
  sourceSha256: string
  originalMarkdown: string
  html: string
  text: string
  sources: Source[]
}
export type LegacyEdition = EditionFields & { kind: "legacy"; format: "editorial-v1" | null }
export type IdentifiedEdition = EditionFields & {
  kind: "identified"
  format: "editorial-v2"
  stories: Story[]
  activeStories: ActiveStory[]
  archivedStories: ArchivedStory[]
  lead: ActiveStory
}
export type Edition = LegacyEdition | IdentifiedEdition
export type EditionInput = { filename: string; text: string }
export type DigestRepository = { sourceRevision: string; editions: Edition[] }

const parser = unified().use(remarkParse)
const reserved = ["In brief", "Archived stories", "Navigation", "Backlinks"]
const marker = /^<!-- story-id: ([a-z0-9]+(?:-[a-z0-9]+)*) -->$/
const execFileAsync = promisify(execFile)
let repository: Promise<DigestRepository> | undefined

function fail(message: string): never {
  throw new Error(message)
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function walk(node: Nodes, callback: (node: Nodes) => void): void {
  callback(node)
  if ("children" in node) node.children.forEach((child) => walk(child, callback))
}

function root(children: RootContent[]): Root {
  return { type: "root", children }
}

function safeUrl(url: string, base = "https://nishantkhurana.me/digests/"): string {
  if (/[\u0000-\u0020\u007f\\]/.test(url)) fail(`unsafe URL: ${url}`)
  if (url.startsWith("#")) return url
  if (url.startsWith("//")) return fail(`unsafe URL: ${url}`)
  let parsed: URL
  try {
    parsed = new URL(url, base)
  } catch {
    return fail(`unsafe URL: ${url}`)
  }
  if (!["https:", "http:", "mailto:"].includes(parsed.protocol)) fail(`unsafe URL: ${url}`)
  if (parsed.username || parsed.password) fail(`unsafe URL credentials: ${url}`)
  return /^[a-z][a-z0-9+.-]*:/i.test(url) ? url : parsed.href
}

function knowledgeLink(value: string): { url: string; label: string } {
  const [target = "", label] = value.split("|", 2)
  if (!target || /[\u0000-\u001f\\]/.test(target) || target.split("/").includes("..")) {
    return fail(`unsafe wikilink: ${value}`)
  }
  const [path = "", fragment] = target.split("#", 2)
  const encoded = path.replace(/\.md$/, "").split("/").map(encodeURIComponent).join("/")
  return {
    url: `https://nishantkhurana.me/${encoded}${fragment ? `#${encodeURIComponent(fragment)}` : ""}`,
    label: label ?? target,
  }
}

function render(children: RootContent[], definitions: Definition[], base: string): string {
  const tree = structuredClone(root([...children, ...definitions]))
  findAndReplace(tree, [
    /\[\[([^\]\n]+)\]\]/g,
    (_match, value: string) => {
      const link = knowledgeLink(value)
      return { type: "link", url: link.url, children: [{ type: "text", value: link.label }] }
    },
  ])
  walk(tree, (node) => {
    if ("url" in node) node.url = safeUrl(node.url, base)
  })
  const html = toHast(tree, {
    handlers: { html: (_state, node) => ({ type: "text", value: node.value }) },
  })
  return toHtml(html, { characterReferences: { useNamedReferences: true } })
}

function sourceLinks(children: RootContent[], definitions: Map<string, Definition>): Source[] {
  const sources: Source[] = []
  walk(root(children), (node) => {
    const url =
      node.type === "link"
        ? node.url
        : node.type === "linkReference"
          ? definitions.get(node.identifier)?.url
          : undefined
    if (url?.startsWith("https://")) sources.push({ label: toString(node), url })
  })
  return sources
}

function plainText(children: RootContent[]): string {
  return children
    .filter((node) => node.type !== "definition" && node.type !== "html")
    .map((node) => toString(node))
    .filter(Boolean)
    .join("\n\n")
}

function markdownFor(children: RootContent[], body: string): string {
  const first = children[0]?.position?.start.offset
  const last = children.at(-1)?.position?.end.offset
  return first === undefined || last === undefined ? "" : body.slice(first, last).trim()
}

function isMarker(node: Nodes): boolean {
  return node.type === "html" && /^\s*<!--\s*story-id:/.test(node.value)
}

function isComment(node: RootContent): boolean {
  return node.type === "html" && node.value.startsWith("<!--") && !isMarker(node)
}

function headingName(node: Heading): string {
  return toString(node)
}

function parseDate(filename: string, value: unknown): string {
  const match = /^x-ai-(\d{4}-\d{2}-\d{2})\.md$/.exec(filename)
  if (!match?.[1] || typeof value !== "string" || value !== match[1]) {
    return fail(`date must match daily filename: ${filename}`)
  }
  const instant = new Date(`${value}T00:00:00.000Z`)
  if (!Number.isFinite(instant.getTime()) || instant.toISOString().slice(0, 10) !== value) {
    return fail(`invalid edition date: ${value}`)
  }
  return value
}

export function parseEdition({ filename, text }: EditionInput): Edition {
  const frontmatter = /^---\n([\s\S]*?)\n---(?:\n|$)/.exec(text)
  if (!frontmatter) return fail(`${filename}: missing edition frontmatter`)
  const document = parseDocument(frontmatter[1], { uniqueKeys: true })
  if (document.errors.length) return fail(`${filename}: ${document.errors[0]?.message}`)
  const metadata: unknown = document.toJS()
  if (!isObject(metadata)) return fail(`${filename}: invalid frontmatter`)
  const date = parseDate(filename, metadata.date)
  if (typeof metadata.title !== "string" || !metadata.title.trim())
    return fail(`${filename}: missing title`)
  const format = "digest_format" in metadata ? metadata.digest_format : null
  if (
    ("digest_format" in metadata && format === null) ||
    (format !== null && format !== "editorial-v1" && format !== "editorial-v2")
  ) {
    return fail(`${filename}: unsupported digest_format: ${String(format)}`)
  }
  const body = text.slice(frontmatter[0].length)
  const tree = parser.parse(body)
  const definitions: Definition[] = []
  const definitionsById = new Map<string, Definition>()
  walk(tree, (node) => {
    if ("url" in node) safeUrl(node.url)
    if (node.type === "definition") {
      if (definitionsById.has(node.identifier))
        fail(`duplicate link definition: ${node.identifier}`)
      definitions.push(node)
      definitionsById.set(node.identifier, node)
    }
  })
  walk(tree, (node) => {
    if (
      (node.type === "linkReference" || node.type === "imageReference") &&
      !definitionsById.has(node.identifier)
    ) {
      fail(`missing link definition: ${node.identifier}`)
    }
  })
  const furniture = tree.children.findIndex(
    (node) =>
      node.type === "heading" &&
      node.depth === 2 &&
      ["Navigation", "Backlinks"].includes(headingName(node)),
  )
  const reading = furniture < 0 ? tree.children : tree.children.slice(0, furniture)
  const path = `/editions/${date}/`
  const renderNodes = (children: RootContent[]) =>
    render(
      children,
      definitions,
      `https://nishantkhurana.me/digests/${filename.replace(/\.md$/, "")}`,
    )
  const common = {
    date,
    title: metadata.title.trim(),
    publishedAt: `${date}T00:00:00+05:30`,
    path,
    readPath: `${path}read/`,
    sourcePath: `content/digests/${filename}`,
    sourceSha256: createHash("sha256").update(text, "utf8").digest("hex"),
    originalMarkdown: text,
  }
  if (format !== "editorial-v2") {
    return {
      ...common,
      kind: "legacy",
      format,
      html: renderNodes(reading),
      text: plainText(reading),
      sources: sourceLinks(reading, definitionsById),
    }
  }

  const headings = tree.children.flatMap((node, index) =>
    node.type === "heading" && [2, 3].includes(node.depth) ? [{ node, index }] : [],
  )
  for (const { node } of headings) {
    const start = node.position?.start
    if (
      !start ||
      start.column !== 1 ||
      !body.slice(start.offset).startsWith(`${"#".repeat(node.depth)} `)
    )
      fail("edition headings must start at column zero")
  }
  const top = headings.filter(({ node }) => node.depth === 2)
  const lastSections = top.slice(-2).map(({ node }) => headingName(node))
  if (top.length < 3 || lastSections[0] !== "Navigation" || lastSections[1] !== "Backlinks") {
    return fail("final sections must be Navigation then Backlinks")
  }
  const first = top[0]
  if (
    !first ||
    reserved.some((name) => name.toLowerCase() === headingName(first.node).toLowerCase()) ||
    tree.children
      .slice(0, first.index)
      .some((node) => node.type !== "definition" && !isComment(node))
  ) {
    return fail("edition must start with its lead story")
  }
  for (const name of reserved) {
    const matches = top.filter(({ node }) => headingName(node).toLowerCase() === name.toLowerCase())
    if (matches.length > 1 || matches.some(({ node }) => headingName(node) !== name))
      fail(`use one exact reserved heading: ${name}`)
  }
  if (
    top.some(({ node }) => headingName(node) === "Archived stories") &&
    top.slice(-3, -2).some(({ node }) => headingName(node) !== "Archived stories")
  ) {
    fail("Archived stories must be the final content section")
  }
  const stories: Story[] = []
  const ids = new Set<string>()
  const consumed = new Set<Nodes>()

  function readStory(heading: Heading, index: number, end: number, kind: Story["kind"]): void {
    const idNode = tree.children[index + 1]
    const id = idNode?.type === "html" ? marker.exec(idNode.value)?.[1] : undefined
    if (
      !id ||
      !idNode ||
      heading.position?.start.column !== 1 ||
      idNode.position?.start.column !== 1 ||
      idNode.position.start.line !== (heading.position?.end.line ?? -1) + 1 ||
      !body
        .slice(heading.position.start.offset, heading.position.end.offset)
        .startsWith(`${"#".repeat(heading.depth)} `)
    ) {
      fail(`${headingName(heading)}: missing or unsafe story-id immediately after heading`)
    }
    if (ids.has(id)) fail(`duplicate story-id: ${id}`)
    ids.add(id)
    consumed.add(idNode)
    let children = tree.children.slice(index + 2, end).filter((node) => node.type !== "definition")
    let correction: string | undefined
    if (kind === "archived") {
      const paragraph = children[0]
      const content = paragraph?.type === "paragraph" ? toString(paragraph) : ""
      if (!content.startsWith("Correction: ") || !content.slice(12).trim() || children.length < 2) {
        fail(`${id}: archived story requires a Correction paragraph and original prose`)
      }
      correction = content.slice(12).trim()
      children = children.slice(1)
    }
    const summaryIndex = children.findIndex((node) => node.type === "paragraph")
    const summaryNode = children[summaryIndex]
    if (!summaryNode || summaryIndex !== 0) fail(`${id}: missing opening summary paragraph`)
    const sources = sourceLinks(children, definitionsById)
    if (!sources.length) fail(`${id}: missing adjacent HTTPS source link`)
    const fields = {
      id,
      headline: headingName(heading),
      path: `${path}stories/${id}/`,
      editionPath: path,
      summary: toString(summaryNode),
      summaryHtml: renderNodes([summaryNode]),
      markdown: markdownFor(children, body),
      bodyMarkdown: markdownFor(children.slice(1), body),
      html: renderNodes(children),
      text: plainText(children),
      sources,
    }
    if (kind === "archived") {
      if (correction === undefined) return fail(`${id}: missing correction`)
      const correctionNode: RootContent = {
        type: "paragraph",
        children: [{ type: "text", value: `Correction: ${correction}` }],
      }
      stories.push({
        ...fields,
        kind,
        correction,
        html: renderNodes([correctionNode, ...children]),
        text: `Correction: ${correction}\n\n${fields.text}`,
      })
    } else stories.push({ ...fields, kind })
  }

  for (const [position, section] of top.entries()) {
    const end = top[position + 1]?.index ?? tree.children.length
    const name = headingName(section.node)
    const children = headings.filter(
      ({ index, node }) => section.index < index && index < end && node.depth === 3,
    )
    if (name === "Navigation" || name === "Backlinks") continue
    if (name === "In brief" || name === "Archived stories") {
      const firstChild = children[0]
      if (
        !firstChild ||
        tree.children
          .slice(section.index + 1, firstChild.index)
          .some((node) => node.type !== "definition" && !isComment(node))
      ) {
        fail(`${name}: requires H3 records without introductory prose`)
      }
      for (const [childPosition, child] of children.entries())
        readStory(
          child.node,
          child.index,
          children[childPosition + 1]?.index ?? end,
          name === "In brief" ? "brief" : "archived",
        )
    } else {
      if (children.length) fail(`${name}: H3 records belong under In brief or Archived stories`)
      readStory(section.node, section.index, end, "story")
    }
  }
  walk(tree, (node) => {
    if (isMarker(node) && !consumed.has(node)) fail("story-id is not attached to a story heading")
  })
  const activeStories = stories.filter((story): story is ActiveStory => story.kind !== "archived")
  const archivedStories = stories.filter(
    (story): story is ArchivedStory => story.kind === "archived",
  )
  const lead = activeStories[0]
  if (!lead || lead.kind !== "story") return fail("editorial-v2 requires a full lead story")
  const activeNodes = reading.filter((node) => !consumed.has(node))
  const archiveIndex = activeNodes.findIndex(
    (node) => node.type === "heading" && headingName(node) === "Archived stories",
  )
  const fullEdition = archiveIndex < 0 ? activeNodes : activeNodes.slice(0, archiveIndex)
  return {
    ...common,
    kind: "identified",
    format,
    stories,
    activeStories,
    archivedStories,
    lead,
    html: renderNodes(fullEdition),
    text: plainText(fullEdition),
    sources: activeStories.flatMap((story) => story.sources),
  }
}

export function parseEditions(inputs: EditionInput[]): Edition[] {
  const editions = inputs.map(parseEdition)
  const dates = new Set<string>()
  for (const edition of editions) {
    if (dates.has(edition.date)) fail(`duplicate edition date: ${edition.date}`)
    dates.add(edition.date)
  }
  return editions.sort((left, right) => right.date.localeCompare(left.date))
}

export function loadDigestRepository(): Promise<DigestRepository> {
  repository ??= (async () => {
    const repositoryRoot = (
      await execFileAsync("git", ["rev-parse", "--show-toplevel"], {
        cwd: process.cwd(),
        encoding: "utf8",
      })
    ).stdout.trim()
    const git = async (args: string[]) =>
      (
        await execFileAsync("git", args, {
          cwd: repositoryRoot,
          encoding: "utf8",
          maxBuffer: 32 * 1024 * 1024,
        })
      ).stdout
    const sourceRevision = (await git(["rev-parse", "HEAD"])).trim()
    const paths = (
      await git(["ls-tree", "-r", "--name-only", "-z", sourceRevision, "--", "content/digests/"])
    )
      .split("\0")
      .filter((path) => /^content\/digests\/x-ai-\d{4}-\d{2}-\d{2}\.md$/.test(path))
    const inputs = await Promise.all(
      paths.map(async (path) => ({
        filename: path.slice("content/digests/".length),
        text: await git(["show", `${sourceRevision}:${path}`]),
      })),
    )
    return { sourceRevision, editions: parseEditions(inputs) }
  })()
  return repository
}

export async function loadEditions(): Promise<Edition[]> {
  return (await loadDigestRepository()).editions
}
