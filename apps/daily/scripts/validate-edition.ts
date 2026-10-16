import { readFile } from "node:fs/promises"
import { basename } from "node:path"
import { parseEdition, validateRevision } from "../../../hermes/ai-x-digest/content/parser.ts"
import { compileEdition } from "../../../hermes/ai-x-digest/content/compiler.ts"

const filename = process.argv[2]
if (!filename) throw new Error("Pass the privately staged Markdown edition path")
const input = {
  filename: basename(filename),
  text: await readFile(filename, "utf8"),
}
compileEdition(input)
const edition = parseEdition(input)
const previousFilename = process.argv[3]
if (previousFilename) {
  const previous = parseEdition({
    filename: basename(previousFilename),
    text: await readFile(previousFilename, "utf8"),
  })
  validateRevision(previous, edition)
}
