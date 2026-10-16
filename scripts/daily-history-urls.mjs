import { readFile } from "node:fs/promises"
import path from "node:path"
import { load as parse } from "js-yaml"
import { unified } from "unified"
import remarkParse from "remark-parse"
import remarkGfm from "remark-gfm"
import smartypants from "remark-smartypants"
import remarkRehype from "remark-rehype"
import rehypeSlug from "rehype-slug"
import { slugifyFilePath, simplifySlug, isRelativeURL } from "../quartz/util/path.ts"

const sources = JSON.parse(await readFile(process.argv[2], "utf8"))
const result = []
for (const { filename, text } of sources) {
  const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)
  const metadata = frontmatter ? parse(frontmatter[1]) : {}
  const raw = metadata.aliases ?? metadata.alias ?? []
  const aliases = (
    Array.isArray(raw)
      ? raw
      : String(raw)
          .split(",")
          .map((value) => value.trim())
  )
    .filter((value) => typeof value === "string" || typeof value === "number")
    .map((value) => slugifyFilePath(String(value) + ".md"))
  if (metadata.permalink) aliases.push(metadata.permalink)
  const canonicalSlug = slugifyFilePath("digests/" + filename)
  const original = simplifySlug(canonicalSlug)
  const aliasSlugs = aliases.map((alias) =>
    isRelativeURL(alias) ? path.posix.normalize(path.posix.join(original, "..", alias)) : alias,
  )
  const processor = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(smartypants)
    .use(remarkRehype)
    .use(rehypeSlug)
  const tree = await processor.run(processor.parse(text.slice(frontmatter?.[0].length ?? 0)))
  const anchors = []
  function visit(node) {
    if (node.type === "element" && /^h[1-6]$/.test(node.tagName) && node.properties.id)
      anchors.push(node.properties.id)
    for (const child of node.children ?? []) visit(child)
  }
  visit(tree)
  result.push({ filename, canonicalSlug, aliasSlugs, anchors })
}
process.stdout.write(JSON.stringify(result) + "\n")
