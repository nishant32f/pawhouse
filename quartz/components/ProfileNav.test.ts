import assert from "node:assert/strict"
import test from "node:test"
import { h } from "preact"
import { render } from "preact-render-to-string"
import ProfileNav from "./ProfileNav"
import { defaultProcessedContent } from "../plugins/vfile"
import { isFilePath, slugifyFilePath } from "../util/path"

test("profile navigation reaches About and Garden from content, folders and tags", () => {
  const pages: [string, string, string?][] = [
    ["index.md", "/", "Garden"],
    ["about.md", "/about", "About"],
    ["wisdom/tech/Linux.md", "/wisdom/tech/Linux", undefined],
    ["wisdom/index.md", "/wisdom/", undefined],
    ["tags/tech.md", "/tags/tech", undefined],
  ]
  for (const [filePath, pageUrl, active] of pages) {
    assert(isFilePath(filePath))
    const [, file] = defaultProcessedContent({ slug: slugifyFilePath(filePath) })
    const html = render(h(ProfileNav(), { fileData: file.data }))
    assert.match(html, /<nav[^>]+aria-label="Site"/)
    const links = [...html.matchAll(/<a([^>]+)>(About|Garden)<\/a>/g)]
    assert.equal(links.length, 2)
    for (const [, attributes, label] of links) {
      const href = attributes.match(/href="([^"]+)"/)?.[1]
      assert(href)
      assert.equal(
        new URL(href, `https://example.com${pageUrl}`).pathname,
        label === "About" ? "/about" : "/",
      )
      assert.match(attributes, /class="internal"/)
      assert.equal(attributes.includes('aria-current="page"'), label === active)
    }
  }
})
